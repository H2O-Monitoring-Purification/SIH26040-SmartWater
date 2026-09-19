import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.schemas.telemetry import SensorReadingCreate
from app.services.telemetry_service import create_sensor_reading


@dataclass
class SensorSnapshot:
    ph: float
    turbidity: float
    tds: float
    temperature: float


# Normal / safe water
NORMAL = SensorSnapshot(
    ph=7.2,
    turbidity=2.5,
    tds=280,
    temperature=26.4,
)


# Unsafe: high turbidity
HIGH_TURBIDITY = SensorSnapshot(
    ph=7.1,
    turbidity=18.0,
    tds=290,
    temperature=26.8,
)


# Unsafe: high TDS
HIGH_TDS = SensorSnapshot(
    ph=7.3,
    turbidity=2.8,
    tds=850,
    temperature=27.0,
)


# Unsafe: high pH
BAD_PH = SensorSnapshot(
    ph=9.4,
    turbidity=3.0,
    tds=300,
    temperature=27.2,
)


def send_snapshot(
    device_id: int,
    snapshot: SensorSnapshot,
):
    """
    Send one complete sensor snapshot through
    the same telemetry service used by the real device.
    """

    # One timestamp for the complete sensor snapshot.
    recorded_at = datetime.now(timezone.utc)

    readings = [
        SensorReadingCreate(
            device_id=device_id,
            sensor_id=1,
            value=snapshot.ph,
            unit="pH",
            recorded_at=recorded_at,
        ),
        SensorReadingCreate(
            device_id=device_id,
            sensor_id=2,
            value=snapshot.turbidity,
            unit="NTU",
            recorded_at=recorded_at,
        ),
        SensorReadingCreate(
            device_id=device_id,
            sensor_id=3,
            value=snapshot.tds,
            unit="ppm",
            recorded_at=recorded_at,
        ),
        SensorReadingCreate(
            device_id=device_id,
            sensor_id=4,
            value=snapshot.temperature,
            unit="C",
            recorded_at=recorded_at,
        ),
    ]

    db = SessionLocal()

    try:
        for data in readings:
            create_sensor_reading(
                db,
                data,
            )

    finally:
        db.close()


def print_snapshot(
    scenario: str,
    snapshot: SensorSnapshot,
):
    """
    Print a readable representation of the simulated data.
    """

    print()
    print("=" * 50)
    print(f"SMART WATER TELEMETRY - {scenario.upper()}")
    print("=" * 50)

    print(f"pH          : {snapshot.ph}")
    print(f"Turbidity   : {snapshot.turbidity} NTU")
    print(f"TDS         : {snapshot.tds} ppm")
    print(f"Temperature : {snapshot.temperature} C")

    print("=" * 50)
    print("Telemetry sent successfully")
    print()


def run_normal(
    device_id: int = 1,
    cycles: int = 5,
    interval_seconds: float = 2,
):
    """
    Continuously send normal water readings.
    """

    print()
    print("Starting normal-water simulation...")
    print()

    for cycle in range(1, cycles + 1):

        send_snapshot(
            device_id,
            NORMAL,
        )

        print(
            f"[Cycle {cycle}/{cycles}] "
            f"pH={NORMAL.ph} | "
            f"Turbidity={NORMAL.turbidity} NTU | "
            f"TDS={NORMAL.tds} ppm | "
            f"Temperature={NORMAL.temperature} C"
        )

        if cycle < cycles:
            time.sleep(interval_seconds)

    print()
    print("Normal simulation completed.")
    print()


def run_scenario(
    scenario: str,
    device_id: int = 1,
):
    """
    Send one predefined water-quality scenario.
    """

    scenarios = {
        "normal": NORMAL,
        "high_turbidity": HIGH_TURBIDITY,
        "high_tds": HIGH_TDS,
        "bad_ph": BAD_PH,
    }

    scenario = scenario.lower().strip()

    snapshot = scenarios.get(
        scenario
    )

    if snapshot is None:
        raise ValueError(
            "Unknown scenario. "
            "Use: normal, high_turbidity, high_tds, bad_ph"
        )

    send_snapshot(
        device_id,
        snapshot,
    )

    print_snapshot(
        scenario,
        snapshot,
    )


def main():
    """
    Command-line entry point.

    Examples:

        python -m app.services.telemetry_simulator normal

        python -m app.services.telemetry_simulator high_turbidity

        python -m app.services.telemetry_simulator high_tds

        python -m app.services.telemetry_simulator bad_ph
    """

    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "normal"
    )

    try:
        run_scenario(
            scenario,
            device_id=1,
        )

    except ValueError as exc:
        print()
        print(f"ERROR: {exc}")
        print()
        sys.exit(1)

    except Exception as exc:
        print()
        print("Telemetry simulation failed.")
        print(f"ERROR: {exc}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()