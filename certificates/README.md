# Use of HTTPS
You need to create the ssl certificates with:
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```