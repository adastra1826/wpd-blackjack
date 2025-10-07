BJ_DB_PATH=local_data/bj.db

# In order to run a local Flask server and send requests over HTTPS to your local machine, you need to create, sign, and trust your own certificates
SSL_PUBLIC_CERT_PATH=local_data/cert.pem
SSL_PRIVATE_KEY_PATH=local_data/key.pem

# Specify the port to run the Flask server on
# If you change this, make sure you update the port number in your Tampermonkey script. The values need to match
PORT=8080