# source .env file
while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ ! $line =~ ^# && $line =~ "=" ]]; then
        export "$line"
    fi
done < .env
npm run dev