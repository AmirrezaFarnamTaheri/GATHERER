import os
import sys
import base64

ARTIFACT_DIR = "persist/artifacts"

def main():
    if not os.path.exists(ARTIFACT_DIR):
        print(f"Error: Artifact directory {ARTIFACT_DIR} does not exist.")
        sys.exit(1)

    files = os.listdir(ARTIFACT_DIR)
    if not files:
        print(f"Error: No artifacts found in {ARTIFACT_DIR}.")
        sys.exit(1)

    print(f"Found {len(files)} artifacts:")
    for f in files:
        path = os.path.join(ARTIFACT_DIR, f)
        size = os.path.getsize(path)
        print(f" - {f}: {size} bytes")
        if size == 0:
            print(f"Error: File {f} is empty.")
            sys.exit(1)

        try:
            with open(path, "rb") as content_file:
                data = content_file.read()

                # Preview raw
                print(f"   Raw Head: {data[:50]}")

                # Try Base64 decode
                try:
                    decoded = base64.b64decode(data, validate=True)
                    print(f"   Base64 Decoded Preview: {decoded[:50]}")
                except Exception:
                    pass

        except Exception as e:
            print(f"   Error reading: {e}")

    print("Verification successful.")

if __name__ == "__main__":
    main()
