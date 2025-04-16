import argparse
import re

# Instruction set encoding table
INSTRUCTION_SET = {
    "NOP": "0000xxxx xxxx xxxx",
    "BRnzp": "0001nzpx iiii iiii",
    "CMP": "0010xxxx dddd ssss",
    "ADD": "0011dddd ssss tttt",
    "SUB": "0100dddd ssss tttt",
    "MUL": "0101dddd ssss tttt",
    "DIV": "0110dddd ssss tttt",
    "LDR": "0111dddd ssss xxxx",
    "STR": "1000xxxx dddd ssss",
    "CONST": "1001dddd iiii iiii",
    "RET": "1111xxxx xxxx xxxx",
}

def parse_instruction(line, labels, current_address):
    """Parse a single assembly instruction and generate binary encoding"""

    # Check if the line is a label
    if line.endswith(":"):
        label_name = line[:-1].strip()
        labels[label_name] = current_address
        return None, None

    # Extract the instruction and operands
    match = re.match(r"(\w+)\s*(.*)", line)
    if not match:
        raise ValueError(f"Unable to parse instruction: {line}")
    
    mnemonic, operands = match.groups()
    operands = operands.split(",") if operands else []

    # Special handling for BRn, BRz, BRp instructions
    if mnemonic.startswith("BR"):
        nzp = ["n", "z", "p"]
        br_flags = ["0", "0", "0"]  # Default all flags to 0
        for char in mnemonic[2:]:  # Check flags after BR
            if char in nzp:
                br_flags[nzp.index(char)] = "1"
            else:
                raise ValueError(f"Unknown BR flag: {char}")
        binary = INSTRUCTION_SET["BRnzp"].replace("nzp", "".join(br_flags))  # Replace nzp flags
    else:
        if mnemonic not in INSTRUCTION_SET:
            raise ValueError(f"Unknown instruction: {mnemonic}")
        binary = INSTRUCTION_SET[mnemonic]
    
    # Replace operands
    for i, operand in enumerate(operands):
        operand = operand.strip()
        if operand.startswith("#"):  # Immediate value
            binary = binary.replace(f"iiii iiii", f"{int(operand[1:]):08b}", 1)
        elif operand.startswith("%"):  # Special registers
            special_registers = {
                "blockIdx": 13,
                "blockDim": 14,
                "threadIdx": 15,
            }
            if operand[1:] in special_registers:
                binary = binary.replace(f"{['dddd', 'ssss', 'tttt'][i]}", f"{special_registers[operand[1:]]:04b}", 1)
            else:
                raise ValueError(f"Unknown special register: {operand}")
        elif operand.startswith("R"):  # General-purpose registers
            binary = binary.replace(f"{['dddd', 'ssss', 'tttt'][i]}", f"{int(operand[1:]):04b}", 1)
        elif operand in labels:  # Jump label
            binary = binary.replace(f"iiii iiii", f"{labels[operand]:08b}", 1)
        else:
            raise ValueError(f"Unable to parse operand: {operand}")

    # Remove unused placeholders
    binary = binary.replace("x", "0").replace(" ", "")
    return binary, line

def assemble(input_file, output_file):
    """Generate a Python file containing a binary instruction array from an assembly file"""
    labels = {}
    instructions = []

    # First pass: record label addresses
    with open(input_file, "r") as infile:
        current_address = 0
        for line in infile:
            line = line.split(";")[0].strip()
            if not line:  
                continue
            if line.endswith(":"):  # Label
                label_name = line[:-1].strip()
                labels[label_name] = current_address
            else:
                instructions.append(line)
                current_address += 1

    # Second pass: parse instructions
    with open(output_file, "w") as outfile:
        outfile.write("# Generated binary instruction array\n")
        outfile.write("program = [\n")

        current_address = 0
        for line in instructions:
            if line.endswith(":"):  # If it's a label
                label_name = line[:-1].strip()
                outfile.write(f"                        # {label_name}:\n")  # Add comment
            else:
                binary, original = parse_instruction(line, labels, current_address)
                if binary:
                    outfile.write(f"    0b{binary}, # {original.strip()}\n")
                    current_address += 1

        outfile.write("]\n")

if __name__ == "__main__":
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser(description="Assemble an assembly file into a Python binary instruction array.")
    parser.add_argument("input_file", help="Path to the input assembly file.")
    parser.add_argument("output_file", help="Path to the output Python file.")
    args = parser.parse_args()

    # 调用 assemble 函数
    assemble(args.input_file, args.output_file)
    print(f"Assembly completed, output file: {args.output_file}")