#!/bin/bash

# Prompt the user for the password
read -sp "Enter the password: " password

# Compute the hash using the provided command
hash=$(echo -n "$password" | iconv -t utf16le | openssl md4)

# Print the resulting hash
echo
echo "MD4 Hash: $hash"