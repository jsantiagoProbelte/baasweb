# baasweb

## Production and Development Environment
Use prod or dev to indicate the environment. Configuration are defined on baaswebapp folder on the files dev.py and prod.py

Notice that manage.py is using the dev.py while wsgi is using the prod.py

This can be overwritten by using the --settings=baaswebapp.[prod|dev]

For instance to run the server from command line pointing to production:
python manage.py runserver --settings=baaswebapp.prod

Same applies to db migrations:
python manage.py makemigrations  --settings=baaswebapp.prod

Because manage.py is using dev, the run commands on the visual study is by default calling dev


## Build and publish
This workflow will build and push a Docker container to an Azure Web App when a commit is pushed to your default branch.
#
# This workflow assumes you have already created the target Azure App Service web app.
# For instructions see https://docs.microsoft.com/en-us/azure/app-service/quickstart-custom-container?tabs=dotnet&pivots=container-linux
#
# To configure this workflow:
#
# 1. Download the Publish Profile for your Azure Web App. You can download this file from the Overview page of your Web App in the Azure Portal.
#    For more information: https://docs.microsoft.com/en-us/azure/app-service/deploy-github-actions?tabs=applevel#generate-deployment-credentials
#
# 2. Create a secret in your repository named AZURE_WEBAPP_PUBLISH_PROFILE, paste the publish profile contents as the value of the secret.
#    For instructions on obtaining the publish profile see: https://docs.microsoft.com/azure/app-service/deploy-github-actions#configure-the-github-secret
#
# 3. Create a GitHub Personal access token with "repo" and "read:packages" permissions. 
#
# 4. Create three app settings on your Azure Web app:
#       DOCKER_REGISTRY_SERVER_URL: Set this to "https://ghcr.io"
#       DOCKER_REGISTRY_SERVER_USERNAME: Set this to the GitHub username or organization that owns the repository
#       DOCKER_REGISTRY_SERVER_PASSWORD: Set this to the value of your PAT token from the previous step
#
# 5. Change the value for the AZURE_WEBAPP_NAME.
#
# For more information on GitHub Actions for Azure: https://github.com/Azure/Actions
# For more information on the Azure Web Apps Deploy action: https://github.com/Azure/webapps-deploy
# For more samples to get started with GitHub Action workflows to deploy to Azure: https://github.com/Azure/actions-workflow-samples


# To make migrations on production:
# python manage.py migrate --database=shhtunnel_db