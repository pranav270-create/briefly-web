if [ "$1" != "" ]; then
    project_name=$1
else
    echo "Please provide a project name"
    exit 1
fi
gcloud config set project $project_name
gcloud auth application-default set-quota-project $project_name
env_vars=$(sed 's/#.*//g' .env | xargs | sed 's/ /,/g')
gcloud run deploy briefly-backend --source . --platform managed --memory=4Gi --min-instances=2 --region us-east4 --allow-unauthenticated --set-env-vars=$env_vars