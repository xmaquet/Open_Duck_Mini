import sys
from .io_adapter import MotorBus

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "COM3"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
    with MotorBus(port, baud).session() as bus:
        ids = bus.scan(range(1, 60))
        print("Found IDs:", ids)

if __name__ == "__main__":
    main()
