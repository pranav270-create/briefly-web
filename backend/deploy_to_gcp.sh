if [ "$1" != "" ]; then
    project_name=$1
    gcloud config set project $project_name
    gcloud auth application-default set-quota-project $project_name
fi
env_vars=$(sed 's/#.*//g' .env | xargs | sed 's/ /,/g')
gcloud run deploy briefly-backend --source . --platform managed --memory=4Gi --min-instances=2 --region us-east4 --allow-unauthenticated --set-env-vars=$env_vars