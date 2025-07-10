echo "Check /get_all_listings..."
for i in $(seq 1 30); do
  # Use -s for silent, -f for fail on HTTP errors (4xx/5xx)
  # Use -w "%{http_code}" to get the HTTP status code
  RESPONSE=$(curl -s -w "%{http_code}" -f http://localhost:5002/get_all_listings)
  HTTP_CODE="${RESPONSE: -3}" # Extract the last 3 characters (HTTP code)
  BODY="${RESPONSE::-3}"      # Get the body (everything before the last 3 chars)

  if [[ "$HTTP_CODE" == "200" ]]; then
    echo "Flask app is ready and /get_all_listings returned 200 OK!"
    break
  fi
  echo "Waiting for Flask app /get_all_listings... (Attempt $i/30, HTTP Code: $HTTP_CODE)"
  sleep 3
done