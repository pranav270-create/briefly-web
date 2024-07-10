# check if docker flag in args
if [ "$1" == "docker" ]; then
    # build docker image
    sudo docker build -t backend:latest .
    # run docker container
    sudo docker run -p 8080:8080 --env-file .env backend:latest
    exit 0
else
    # source .env file
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ ! $line =~ ^# && $line =~ "=" ]]; then
            export "$line"
        fi
    done < .env
    # run server locally
    python3 main.py
fi