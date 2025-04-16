
signal = """B0 06 00 00 00 00 C8 07 00 00 01 00 00 00 00 00 00 00 00 00 00
B0 99 0F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
A0 04 01 48 01 54 01 87 01 C6 01 2C 02 7E 02 AD 02 0D 03 7B 03
A0 D4 03 34 04 A0 04 14 05 74 05 D9 05 5D 06 CB 06 4B 07 BC 07
B0 0C 27 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"""

# example packet
# B0 01 00 00 00 01 03 00 00 00 00 01 07 00 00 00 01 0A 00 00 01
# 1us : high
# 3us : low
# 7us : high
# 10us : low
# 1 2 3 4 5 6 7 8 9 10 : in us 
# 1 1 0 0 0 0 1 1 1 0 : state  --> this is our goal, an array of bits array

def split_into_packets(signal_str):
    lines = signal_str.strip().splitlines()
    hex_values = []
    for line in lines:
        hex_values.extend(line.strip().split())

    packets = []
    i = 0
    while i < len(hex_values):
        if hex_values[i] == 'B0':
            packet = hex_values[i+1:i+21]  # skip 'B0', get 20 bytes
            if len(packet) == 20:
                packets.append(packet)
            i += 21
        else:
            i += 1
    return packets


def extract_subpackets(packet):
    subpackets = []
    for i in range(0, 20, 5):
        subpacket = packet[i:i+5]
        if len(subpacket) == 5 and "".join(subpacket) != "0000000000":
            subpackets.append(subpacket)
    return subpackets


def decode_subpacket(subpacket):
    timestamp_bytes = subpacket[0:4]
    state_byte = subpacket[4]
    timestamp = int(''.join(reversed(timestamp_bytes)), 16)
    state = int(state_byte, 16)
    return (timestamp, state)


def build_state_array(subpackets):
    # Sort by timestamp
    transitions = [decode_subpacket(sp) for sp in subpackets]
    transitions.sort()

    max_time = max(t[0] for t in transitions) if transitions else 0
    states = [0] * (max_time + 1)

    current_state = 0
    for t, s in transitions:
        current_state = s
        for i in range(t, len(states)):
            states[i] = current_state

    return states

def print_transitions(packet):
    subpackets = extract_subpackets(packet)
    transitions = [decode_subpacket(sp) for sp in subpackets]
    transitions.sort()  # Ensure sorted by time

    for timestamp, state in transitions:
        state_str = 'high' if state == 1 else 'low'
        print(f"{timestamp}us : {state_str}")

def process_signal(signal_str):
    packets = split_into_packets(signal_str)
    all_bit_arrays = []

    for packet in packets:
        subpackets = extract_subpackets(packet)
        print_transitions(packet)
        bit_array = build_state_array(subpackets)
        all_bit_arrays.append(bit_array)

    return all_bit_arrays


result = process_signal(signal)
# for i, bits in enumerate(result):
#     print(f"Packet {i + 1}: {bits}")




