from utils.clientCertAuth import list_client_certs, revoke_client_cert


def revoke_client_cert_cli():
    print("Presiona CTRL+C para salir.\n")

    while True:
        try:
            certs = [c for c in list_client_certs() if not c["revoked"]]
            if not certs:
                print("No hay certificados activos.")
                return

            print("Certificados activos:")
            for i, c in enumerate(certs):
                print(f"  [{i}] {c['username']} ({c['label']}) - serial {c['serial']} - emitido {c['issued_at']}")

            choice = input("\nÍndice a revocar (o vacío para salir): ").strip()
            if not choice:
                break
            try:
                selected = certs[int(choice)]
            except (ValueError, IndexError):
                print("❌ Índice no válido.")
                continue

            revoke_client_cert(selected["serial"])
            print(f"✅ Certificado de '{selected['username']}' ({selected['label']}) revocado.\n")

        except KeyboardInterrupt:
            print("\nSaliendo...")
            break


if __name__ == "__main__":
    revoke_client_cert_cli()
