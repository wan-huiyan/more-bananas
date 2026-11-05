// heat: one line for memlog.py, "thermal_state,fan_rpm,fan_max_rpm,chip_temp_c" (-1 when this Mac does not report it).
// Reads only what macOS gives any user without admin rights: the thermal state, the fan from the SMC, and the
// chip's temperature sensors. Built by install.sh with swiftc (Xcode command line tools); memlog.py skips it if missing.
// Run with -v to list every temperature sensor.
import Foundation
import IOKit

let state = ["nominal", "fair", "serious", "critical"][min(ProcessInfo.processInfo.thermalState.rawValue, 3)]

// --- Fan: SMC keys F0Ac (current) and F0Mx (maximum). The structs mirror the C layout byte for byte (80 bytes);
// Swift packs a nested struct to its size, not its stride, so SMCKeyInfo carries its trailing padding explicitly.
struct SMCVers { var major: UInt8 = 0, minor: UInt8 = 0, build: UInt8 = 0, reserved: UInt8 = 0, release: UInt16 = 0 }
struct SMCPLimit { var version: UInt16 = 0, length: UInt16 = 0, cpu: UInt32 = 0, gpu: UInt32 = 0, mem: UInt32 = 0 }
struct SMCKeyInfo { var size: UInt32 = 0, type: UInt32 = 0, attributes: UInt8 = 0, pad0: UInt8 = 0, pad1: UInt8 = 0, pad2: UInt8 = 0 }
struct SMCParam {
  var key: UInt32 = 0; var vers = SMCVers(); var limit = SMCPLimit(); var info = SMCKeyInfo()
  var result: UInt8 = 0, status: UInt8 = 0, command: UInt8 = 0; var data32: UInt32 = 0
  var bytes: (UInt64, UInt64, UInt64, UInt64) = (0, 0, 0, 0)
}
func smcNumber(_ conn: io_connect_t, _ key: String) -> Double? {
  var inp = SMCParam(), out = SMCParam(), size = MemoryLayout<SMCParam>.stride
  inp.key = key.utf8.reduce(0) { $0 << 8 | UInt32($1) }; inp.command = 9          // 9: read the key's type and size
  guard IOConnectCallStructMethod(conn, 2, &inp, size, &out, &size) == kIOReturnSuccess, out.result == 0 else { return nil }
  let info = out.info; inp.info.size = info.size; inp.command = 5; out = SMCParam()  // 5: read its bytes
  guard IOConnectCallStructMethod(conn, 2, &inp, size, &out, &size) == kIOReturnSuccess, out.result == 0 else { return nil }
  let b = withUnsafeBytes(of: out.bytes) { Array($0.prefix(Int(info.size))) }
  switch info.type {
  case 0x666c7420 where b.count == 4: return Double(b.withUnsafeBytes { $0.load(as: Float.self) })  // "flt " (Apple silicon)
  case 0x66706532 where b.count == 2: return Double(UInt16(b[0]) << 8 | UInt16(b[1])) / 4             // "fpe2" (Intel)
  default: return nil
  }
}
var fan = -1.0, fanMax = -1.0
let smc = IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("AppleSMC"))
var conn: io_connect_t = 0
if smc != 0 && IOServiceOpen(smc, mach_task_self_, 0, &conn) == kIOReturnSuccess {
  if (smcNumber(conn, "FNum") ?? 1) > 0 {   // FNum is a byte, so this reads nil; a fanless Mac simply has no F0Ac
    fan = smcNumber(conn, "F0Ac") ?? -1; fanMax = smcNumber(conn, "F0Mx") ?? -1
  }
  IOServiceClose(conn)
}

// --- Chip temperature: the hottest processor-cluster sensor from the HID temperature services.
@_silgen_name("IOHIDEventSystemClientCreate") func hidClient(_ a: CFAllocator?) -> Unmanaged<AnyObject>?
@_silgen_name("IOHIDEventSystemClientSetMatching") func hidMatch(_ c: AnyObject, _ m: CFDictionary) -> Int32
@_silgen_name("IOHIDEventSystemClientCopyServices") func hidServices(_ c: AnyObject) -> Unmanaged<CFArray>?
@_silgen_name("IOHIDServiceClientCopyEvent") func hidEvent(_ s: AnyObject, _ t: Int64, _ a: Int32, _ b: Int64) -> Unmanaged<AnyObject>?
@_silgen_name("IOHIDServiceClientCopyProperty") func hidProperty(_ s: AnyObject, _ k: CFString) -> Unmanaged<AnyObject>?
@_silgen_name("IOHIDEventGetFloatValue") func hidFloat(_ e: AnyObject, _ f: Int32) -> Double
var temps: [(String, Double)] = []
if let c = hidClient(kCFAllocatorDefault)?.takeRetainedValue() {
  _ = hidMatch(c, ["PrimaryUsagePage": 0xff00, "PrimaryUsage": 5] as CFDictionary)
  for s in (hidServices(c)?.takeRetainedValue() as? [AnyObject]) ?? [] {
    let name = (hidProperty(s, "Product" as CFString)?.takeRetainedValue() as? String) ?? "?"
    if let e = hidEvent(s, 15, 0, 0)?.takeRetainedValue() {
      let t = hidFloat(e, 15 << 16); if t > 0 && t < 130 { temps.append((name, t)) }
    }
  }
}
let chip = temps.filter { ["pACC", "eACC", "tdie", "SOC", "CPU"].contains(where: $0.0.contains) }.map { $0.1 }
let hottest = (chip.isEmpty ? temps.map { $0.1 } : chip).max() ?? -1
if CommandLine.arguments.contains("-v") { for (n, t) in temps.sorted(by: { $0.1 > $1.1 }) { print(n, String(format: "%.1f", t)) } }
print("\(state),\(Int(fan.rounded())),\(Int(fanMax.rounded())),\(String(format: "%.1f", hottest))")
