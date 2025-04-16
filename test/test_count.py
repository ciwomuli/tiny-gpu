import cocotb
from cocotb.triggers import RisingEdge
from .helpers.setup import setup
from .helpers.memory import Memory
from .helpers.format import format_cycle
from .helpers.logger import logger
from .test_count_program import program

@cocotb.test()
async def test_count(dut):
    # Program Memory
    program_memory = Memory(dut=dut, addr_bits=8, data_bits=16, channels=1, name="program")

    # Data Memory
    data_memory = Memory(dut=dut, addr_bits=8, data_bits=8, channels=4, name="data")
    data = [
        0, 1, 2, 3, 4, 5, 6, 7,
        0, 8, 2, 8, 2, 4, 9, 0,
        0, 6, 5, 4, 3, 2, 1, 0,
        0, 2, 9, 2, 5, 6, 2, 3,
        0, 1, 2, 3, 4, 5, 6, 7,
        0, 8, 2, 8, 2, 4, 9, 0,
        0, 6, 5, 4, 3, 2, 1, 0,
        0, 2, 9, 2, 5, 6, 2, 3,
    ]

    # Device Control
    threads = 8

    await setup(
        dut=dut,
        program_memory=program_memory,
        program=program,
        data_memory=data_memory,
        data=data,
        threads=threads
    )

    data_memory.display(64)

    cycles = 0
    while dut.done.value != 1:
        data_memory.run()
        program_memory.run()

        await cocotb.triggers.ReadOnly()
        format_cycle(dut, cycles)
        
        await RisingEdge(dut.clk)
        cycles += 1

    logger.info(f"Completed in {cycles} cycles")
    data_memory.display(64)

    expected_results = []
    for block_start in range(0, 32, 8):  # 每个块大小为 8
        count = sum(1 for x in data[block_start + 1:block_start + 8] if x >= 5)  # 后面 8 个元素中大于 5 的数量
        expected_results.append(count)
        
    for block_start in range(32, 64, 8):  # 每个块大小为 8
        count = sum(data[block_start + 1:block_start + 8])  # 后面 8 个元素的和
        expected_results.append(count)

    for i, expected in enumerate(expected_results):
        result = data_memory.memory[i * 8]
        assert result == expected, f"Result mismatch at block {i}: expected {expected}, got {result}"