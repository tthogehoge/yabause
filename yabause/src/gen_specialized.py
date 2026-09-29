import struct
import argparse
from pathlib import Path

source_dir = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--capture", default="scu_dsp_capture_06.bin")
parser.add_argument("--output")
parser.add_argument("--macro-prefix")
args = parser.parse_args()
capture_path = source_dir / args.capture
capture_stem = capture_path.stem.replace("scu_dsp_capture_", "")
macro_prefix = args.macro_prefix or (
    "SCU_DSP_SPECIALIZED_GRANDIA"
    if capture_stem == "06" else f"SCU_DSP_SPECIALIZED_{capture_stem}"
)

with capture_path.open("rb") as f:
    data = f.read()
words = struct.unpack("<256I", data)

def disd1bussrc_expr(num):
    return f"readgensrc_specialized(0x{num:X})"

def gen_operation(addr, instruction):
    lines = []
    alu = (instruction >> 26) & 0x3F
    p = (instruction >> 23) & 0x3
    a = (instruction >> 17) & 0x3
    d1 = (instruction >> 12) & 0x3
    uses_alu = alu not in (0, 6)
    if alu == 0:
        uses_alu = (
            a == 2
            or (p == 3 and ((instruction >> 20) & 0x7) in (0x9, 0xA))
            or ((instruction >> 23) & 0x4 and ((instruction >> 20) & 0x7) in (0x9, 0xA))
            or ((instruction >> 17) & 0x4 and ((instruction >> 14) & 0x7) in (0x9, 0xA))
            or (d1 == 3 and (instruction & 0xF) in (0x9, 0xA))
            or (a == 3 and ((instruction >> 14) & 0x7) in (0x9, 0xA))
        )
    if uses_alu:
        lines.append("ScuDsp->ALU.all = ScuDsp->AC.all;")
    # ALU op (mirrors the branchless ALU switch, case bodies unchanged,
    # just emitted unconditionally since alu is a compile-time constant here)
    if alu == 0x1:
        lines.append("ScuDsp->ALU.part.L = (s64)((u32)ScuDsp->AC.part.L & (u32)ScuDsp->P.part.L);")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((s64)ScuDsp->ALU.part.L < 0);")
        lines.append("ScuDsp->ProgControlPort.part.C = 0;")
    elif alu == 0x2:
        lines.append("ScuDsp->ALU.part.L = (u64)((u32)ScuDsp->AC.part.L | (u32)ScuDsp->P.part.L);")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((s64)ScuDsp->ALU.part.L < 0);")
        lines.append("ScuDsp->ProgControlPort.part.C = 0;")
    elif alu == 0x3:
        lines.append("ScuDsp->ALU.part.L = (u64)((u32)ScuDsp->AC.part.L ^ (u32)ScuDsp->P.part.L);")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((s64)ScuDsp->ALU.part.L < 0);")
        lines.append("ScuDsp->ProgControlPort.part.C = 0;")
    elif alu == 0x4:
        lines.append("ScuDsp->ALU.part.L = (s32)ScuDsp->AC.part.L + (s32)ScuDsp->P.part.L;")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((s32)ScuDsp->ALU.part.L < 0);")
        lines.append("ScuDsp->ProgControlPort.part.C = ((((u64)(u32)ScuDsp->P.part.L + (u64)(u32)ScuDsp->AC.part.L) & 0x100000000) != 0);")
    elif alu == 0x5:
        lines.append("ScuDsp->ALU.part.L = (s32)ScuDsp->AC.part.L - (s32)ScuDsp->P.part.L;")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((s64)ScuDsp->ALU.part.L < 0);")
        lines.append("ScuDsp->ProgControlPort.part.C = ((((u64)(u32)ScuDsp->AC.part.L - (u64)(u32)ScuDsp->P.part.L)) & 0x100000000) != 0;")
    elif alu == 0x6:
        lines.append("ScuDsp->ALU.all = (s64)ScuDsp->AC.all + (s64)ScuDsp->P.all;")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.all == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((ScuDsp->ALU.all & 0x800000000000) != 0);")
        lines.append("ScuDsp->ProgControlPort.part.C = ((((ScuDsp->AC.all & 0xffffffffffff) + (ScuDsp->P.all & 0xffffffffffff)) & (0x1000000000000)) != 0);")
    elif alu == 0x8:
        lines.append("ScuDsp->ProgControlPort.part.C = ScuDsp->AC.part.L & 0x1;")
        lines.append("ScuDsp->ALU.part.L = (ScuDsp->AC.part.L & 0x80000000) | (ScuDsp->AC.part.L >> 1);")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((ScuDsp->ALU.part.L & 0x80000000) != 0);")
    elif alu == 0x9:
        lines.append("ScuDsp->ProgControlPort.part.C = ScuDsp->AC.part.L & 0x1;")
        lines.append("ScuDsp->ALU.part.L = ((u32)(ScuDsp->ProgControlPort.part.C) << 31) | ((u32)(ScuDsp->AC.part.L) >> 1);")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((ScuDsp->ALU.part.L & 0x80000000) != 0);")
    elif alu == 0xA:
        lines.append("ScuDsp->ProgControlPort.part.C = (ScuDsp->AC.part.L >> 31) & 0x01;")
        lines.append("ScuDsp->ALU.part.L = (u32)(ScuDsp->AC.part.L << 1);")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((ScuDsp->ALU.part.L & 0x80000000) != 0);")
    elif alu == 0xB:
        lines.append("ScuDsp->ProgControlPort.part.C = (ScuDsp->AC.part.L >> 31) & 0x01;")
        lines.append("ScuDsp->ALU.part.L = (((u32)ScuDsp->AC.part.L << 1) | ScuDsp->ProgControlPort.part.C);")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((ScuDsp->ALU.part.L & 0x80000000) != 0);")
    elif alu == 0xF:
        lines.append("ScuDsp->ProgControlPort.part.C = (ScuDsp->AC.part.L >> 24) & 0x01;")
        lines.append("ScuDsp->ALU.part.L = ((u32)(ScuDsp->AC.part.L << 8) | ((ScuDsp->AC.part.L >> 24) & 0xFF));")
        lines.append("ScuDsp->ProgControlPort.part.Z = (ScuDsp->ALU.part.L == 0);")
        lines.append("ScuDsp->ProgControlPort.part.S = ((ScuDsp->ALU.part.L & 0x80000000) != 0);")
    # alu == 0 (NOP) or other -> nothing

    # P-write
    if p == 2:
        lines.append("ScuDsp->P.all = (s64)ScuDsp->RX * (s32)ScuDsp->RY;")
    elif p == 3:
        lines.append(f"ScuDsp->P.all = (s64)(s32){disd1bussrc_expr((instruction>>20)&0x7)};")

    # X-bus
    if (instruction >> 23) & 0x4:
        lines.append(f"ScuDsp->RX = {disd1bussrc_expr((instruction>>20)&0x7)};")

    # Y-bus
    if (instruction >> 17) & 0x4:
        lines.append(f"ScuDsp->RY = {disd1bussrc_expr((instruction>>14)&0x7)};")

    # A-write
    if a == 1:
        lines.append("ScuDsp->AC.all = 0;")
    elif a == 2:
        lines.append("ScuDsp->AC.all = ScuDsp->ALU.all;")
    elif a == 3:
        lines.append(f"ScuDsp->AC.all = (s64)(s32){disd1bussrc_expr((instruction>>14)&0x7)};")

    # D1-bus
    if d1 == 1:
        imm = instruction & 0xFF
        lines.append(f"writed1busdest_specialized(0x{(instruction>>8)&0xF:X}, (u32)(signed char)0x{imm:X});")
    elif d1 == 3:
        lines.append(f"writed1busdest_specialized(0x{(instruction>>8)&0xF:X}, {disd1bussrc_expr(instruction&0xF)});")

    if not lines:
        lines.append("/* NOP */")
    return lines

def gen_load_immediate(addr, instruction):
    lines = []
    dest = (instruction >> 26) & 0xF
    if (instruction >> 25) & 1:
        cond = (instruction >> 19) & 0x3F
        val = (instruction & 0x7FFFF) | (0xFFF80000 if (instruction & 0x40000) else 0)
        cond_expr = {
            0x01: "!ScuDsp->ProgControlPort.part.Z",
            0x02: "!ScuDsp->ProgControlPort.part.S",
            0x03: "(ScuDsp->ProgControlPort.part.Z == 0 && ScuDsp->ProgControlPort.part.S == 0)",
            0x04: "!ScuDsp->ProgControlPort.part.C",
            0x08: "!ScuDsp->ProgControlPort.part.T0",
            0x21: "ScuDsp->ProgControlPort.part.Z",
            0x22: "ScuDsp->ProgControlPort.part.S",
            0x23: "(ScuDsp->ProgControlPort.part.Z || ScuDsp->ProgControlPort.part.S)",
            0x24: "ScuDsp->ProgControlPort.part.C",
            0x28: "ScuDsp->ProgControlPort.part.T0",
        }.get(cond)
        if cond_expr is None:
            lines.append(f"/* unknown MVI cond 0x{cond:X} - should not happen for a matched program */")
        else:
            lines.append(f"if ({cond_expr}) writeloadimdest_specialized(0x{dest:X}, (u32)0x{val & 0xFFFFFFFF:08X});")
    else:
        value = instruction & 0x1FFFFFF
        if value & 0x1000000:
            value |= 0xfe000000
        lines.append(f"writeloadimdest_specialized(0x{dest:X}, (u32)0x{value & 0xFFFFFFFF:08X});")
    return lines

out = []
out.append(f"// AUTO-GENERATED by gen_specialized.py from {args.capture}")
out.append("// DO NOT EDIT BY HAND - regenerate from the capture instead.")
out.append("//")
out.append("// One switch case per ProgramRam address, valid ONLY when the currently")
out.append("// loaded program matches GRANDIA_DSP_PROGRAM_HASH. Each function reproduces")
out.append("// exactly what the interpreter's Operation Command / Load Immediate Command")
out.append("// switch would do for that address's known, fixed instruction word - with")
out.append("// all bitfield decoding resolved at generation time instead of at runtime.")
out.append("//")
out.append("// DMA / Jump / Other commands are intentionally NOT specialized here.")
out.append("// The generated macro jumps directly to the common instruction epilogue")
out.append("// for specialized addresses; other addresses fall back to the interpreter.")
out.append("")

specialized_addrs = []

for addr, instruction in enumerate(words):
    top = instruction >> 30
    if top == 0x00:
        body = gen_operation(addr, instruction)
        kind = "OP"
    elif top == 0x02:
        body = gen_load_immediate(addr, instruction)
        kind = "MVI"
    else:
        body = None
        kind = None

    if body is None:
        continue

    specialized_addrs.append(addr)
out.append(f"#define {macro_prefix}_STEP() do {{ \\")
out.append("   switch (ScuDsp->PC) { \\")
for addr in specialized_addrs:
    instruction = words[addr]
    body = gen_operation(addr, instruction) if instruction >> 30 == 0x00 else gen_load_immediate(addr, instruction)
    out.append(f"   case 0x{addr:02X}: {{ \\")
    for line in body:
        out.append(f"      {line} \\")
    out.append("      goto scu_dsp_instruction_complete; \\")
    out.append("   } \\")
out.append("   default: break; \\")
out.append("   } \\")
out.append("} while (0)")


output_path = source_dir / (args.output or (
    "scu_dsp_specialized_grandia.inc.c"
    if capture_stem == "06"
    else f"scu_dsp_specialized_{capture_stem}.inc.c"
))
with output_path.open("w") as f:
    f.write("\n".join(out) + "\n")

specialized_count = len(specialized_addrs)
print(f"Generated {specialized_count} specialized functions out of 256 addresses.")
print(f"Non-specialized (fall back to interpreter): {256-specialized_count}")
