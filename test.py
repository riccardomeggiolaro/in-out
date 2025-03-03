import bcrypt

def hash_password(password: str):
    	# Convert password to bytes and generate salt
	password_bytes = password.encode('utf-8')

	salt = "$2b$12$PAHE4kh6lnXo3w9SF9tj7O".encode('utf-8')

	# Hash the password with the generated salt
	hashed_password = bcrypt.hashpw(password_bytes, salt)

	return hashed_password.decode('utf-8')

print(hash_password("admin"))