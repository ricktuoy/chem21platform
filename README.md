# Chem21 CMS

## Deploying to AWS - step-by-step

Note that you'll want separate S3 buckets and EB deployments for each environment (production, staging, etc)
These notes assume knowledge of AWS S3, IAM, Elastic Beanstalk. Also Python/Django development (inc. virtual environments, virtualenvwrapper, etc)

Some/all of this infrastructure deployment process could probably be automated as a Cloudformation stack/equivalent.

### Set up the published site bucket with static resources
_note that this part won't be needed for production as there's already a bucket set up_

1. Create an S3 bucket for the published site.  Set it up to serve a public website. 
2. Create an IAM deployment user/role for yourself, that has read-right permissions on the bucket
3. Download and configure the AWS CLI if you haven't
4. Set up a local Python virtualenv for the app, using requirements.txt in the repository.
5. Set yourself up to run the requireJS optimiser from the top level of the checked out repository.  It's easiest to do this with node: `npm install -g requirejs`
6. At the top level of this repository, run the following commands to collect, build and deploy all static resources:

``` python manage.py collectstatic `
r.js -o require-build.js `
aws s3 sync collected-static/deploy/ s3://<BUCKET_NAME>/static/ ```

### Deploy the CMS to AWS Elastic Beanstalk

1. Create / amend deployment user or role for yourself, to give it read-right permissions on the site bucket, and permissions to create Elastic Beanstalk environments and deploy to them
2. Follow AWS instructions to install the EB CLI and set up a CodeCommit repository for the CMS
3. Run e.g. `eb create chem21-cms-staging` (replace the environment name with something appropriate)
4. Add a small Postgresql RDS to the new environment in the AWS console (TODO: this can probably be added into the .ebextensions scripts)
5. Create an IAM user for the app that has read-right permissions on the bucket, generate an access key for it.  You will need the access key ID and secret for the next step.
6. You now need to set up environment variables on the EB environment.  These are described below; there is a template Linux shell script at the top level (`setenv.template.sh`) that you can copy to `setenv.sh`, which is gitignored, and populate with your own settings.  Give it execute permissions then run `./setenv.sh` to update the EB environment.
7. Run `eb deploy`.  Once it's deployed the CMS should now be available at the EB environment URL.  The superusers you set up in the env variables will now be able to log in to the CMS and publish the site to the bucket.

### Environment variables

The `setenv.template.sh` template contains the details of all needed env variables, which you can populate with your own settings.
A quick description:

#### Django secret key

```
SECRET_KEY=<UNIQUE_APP_KEY>
```


#### Enable elasticbeanstalk.com domains:

```
DJANGO_AWS_EB_TEST = 1
```

#### PDF generation
```
WKHTMLTOPDF_CMD = wkhtmltopdf
```

#### AWS S3 access
(used by django-storages/s3boto to treat S3 bucket as a file storage)
See deployment instructions above for setting up the access credentials.
```AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME
AWS_STORAGE_REGION
```

#### Google Oauth 2
See below for setting up Google API credentials

```SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET
```

### Google API Oauth2 config

- Create a project in the Google API console 
- Set up an OAuth consent screen

- Under credentials, create an OAuth Client ID with application type "Web application" and the required authorised redirect URIs.  

Redirect URIs will be, for any domains you need to use authentication on: 
- <CMS_DOMAIN>/complete/google-oauth2
- <CMS_DOMAIN>/complete/google-oauth2/

Once the client has been created, you will be shown the key and secret for social auth environment vars as described above.
