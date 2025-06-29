echo "Attempting to connect to PostgreSQL..."
for i in $(seq 1 10); do
  nc -z localhost 5432 && echo "PostgreSQL is ready!" && break
  echo "Waiting for PostgreSQL... ($i/10)"
  sleep 3
done
nc -z localhost 5432 || (echo "PostgreSQL did not become ready after waiting." && exit 1)