"""Command line entrypoint for Kindle capture."""

from __future__ import annotations

from . import capture, config, pdf


def main() -> None:
    try:
        settings = config.get_config_from_user()
        capture.prepare_folder(settings["images_dir"])
        capture.capture_pages(settings)
        pdf.images_to_pdf(settings)
        print("Capture and PDF generation completed successfully.")
    except KeyboardInterrupt:
        print("Capture interrupted by user.")
    except Exception as exc:  # noqa: BLE001
        print(f"An error occurred: {exc}")


if __name__ == "__main__":
    main()
