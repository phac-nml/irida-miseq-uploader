import ast
import json
import httplib

import sys
sys.path.append("../")

from requests import Request
from requests.exceptions import HTTPError as request_HTTPError
from urllib2 import Request, urlopen, URLError, HTTPError


from rauth import OAuth2Service, OAuth2Session

from Model.ValidationResult import ValidationResult
from Exceptions.ProjectError import ProjectError
from Validation.offlineValidation import validateURLForm

clientId="testClient"
clientSecret="testClientSecret"

MAX_TIMEOUT_WAIT=30


def createSession(baseURL, username, password):

    vRes=validateURLForm(baseURL)
    if vRes.isValid():
        oauth_service=get_oauth_service(baseURL)
        access_token=get_access_token(oauth_service, username, password)
        session=oauth_service.get_session(access_token)
    else:
        raise URLError(vRes.getErrors())

    return session

def validateURLexistance(url):
    """
        tries to validate existance of given url by trying to open it
        the passed url are assumed to have passed validation via validateURLForm
        expecting to receive status_code 401/UNAUTHORIZED when trying to validate baseURL/api

        arguments:
            url -- the url link to open and validate

        returns ValidationResult object - stores bool valid and list of string error messages
    """

    #move later to Validation/onlineValidation.py ?


    vRes=ValidationResult()
    valid=True

    try:
        response = urlopen(url, timeout=MAX_TIMEOUT_WAIT)

    except HTTPError, e:

        if hasattr(e,'code'):
            if e.code!=httplib.OK and e.code!=httplib.UNAUTHORIZED :
                msg="Failed to reach " + url +"\n"
                msg=msg + 'Error code: ' + str(e.code)
                valid=False


                if hasattr(e, 'reason'):
                    if len(str(e.reason))>0:
                        msg= msg + ". " + str(e.reason)

                vRes.addErrorMsg( msg )

        else:
            msg="Failed to reach " + url +"\n"
            vRes.addErrorMsg( msg )

    vRes.setValid(valid)

    return vRes

def get_oauth_service(baseURL):
    """
        get oauth service to be used to get access token
        checks if baseURL is valid and checks if baseURL/oauth/token is also valid.
        accessTokenUrl = baseURL + "oauth/token"
        Raises request_HTTPError if accessTokenUrl.

        argument:
            baseURL -- URL of IRIDA server API

        returns oauthService
    """

    accessTokenUrl = baseURL + "oauth/token"

    vRes=validateURLexistance(accessTokenUrl)
    if vRes.isValid():
        oauth_serv = OAuth2Service(
        client_id=clientId,
        client_secret=clientSecret,
        name="irida",
        access_token_url = accessTokenUrl,
        base_url=baseURL)

    else:
        raise request_HTTPError(vRes.getErrors())

    return oauth_serv

def get_access_token(oauth_service, username, password):
    """
        get access token to be used to get session from oauth_service

        arguments:
            oauth_service -- O2AuthService from get_oauth_service
            username -- username for IRIDA
            password -- password for given IRIDA username

        returns access token
    """

    params = {'data' : {'grant_type' : 'password',
        'client_id' : clientId,
        'client_secret' : clientSecret,
        'username' : username,
        'password' : password}}

    access_token =    oauth_service.get_access_token(decoder=decoder,**params)

    return access_token

def decoder(return_dict):
    """
        safely parse given dictionary

        arguments:
            return_dict -- access token dictionary

        returns evaluated dictionary
    """

    irida_dict = ast.literal_eval(return_dict)
    return irida_dict


def getProjects(session, baseURL):
    """
        API call to api/projects to get list of projects

        arguments:
            session -- opened OAuth2Session

        returns list containing projects. each project is a dictionary.
    """

    result=None

    url=baseURL+"projects"
    vRes=validateURLexistance(url)

    if vRes.isValid():
        response = session.get(url)
        result = response.json()["resource"]["resources"]
    else:
        print vRes.getErrors()
    return result


def getSamples(session, projectID):
    """
        API call to api/projects/projectID/samples

        arguments:
            session -- opened OAuth2Session
            projectID -- project ID/ 'identifier' which is just a number

        returns list of samples for the given projectID. each sample is a dictionary
    """

    url=baseURL+"projects/"+projectID+"/samples"
    response = session.get(url)
    if response.status_code==httplib.OK:
        result = response.json()["resource"]["resources"]

    elif response.status_code==httplib.NOT_FOUND:
        raise request_HTTPError("The given project ID doesn't exist")

    else:
        raise request_HTTPError("Error: "+response.status_code+ " " + response.reason)

    return result


def does_projectID_exist(session,projectID):
    retVal=False
    projectsList=getProjects(session)

    for project in projectsList:
        if project['identifier']==projectID:
            retVal=True
            break

    return retVal

def does_sampleID_exist(session,projectID,sampleID):
    retVal=False
    samplesList=getSamples(session,projectID)

    for sample in samplesList:
        if sample['identifier']==sampleID:
            retVal=True
            break

    return retVal

def getSequenceFiles(session, projectID, sampleID):
    """
        API call to api/projects/projectID/sampleID/sequenceFiles

        arguments:
            session -- opened OAuth2Session
            projectID -- project ID/ 'identifier' which is just a number

        returns list of sequenceFiles for given sampleID
    """

    url=baseURL+"projects/"+projectID+"/samples/"+sampleID+"/sequenceFiles"

    response = session.get(url)

    if response.status_code==httplib.OK:
        result = response.json()["resource"]["resources"]

    elif response.status_code==httplib.NOT_FOUND:
        if does_projectID_exist(session, projectID)==False:
            raise request_HTTPError("The given project ID doesn't exist")
        else:
            raise request_HTTPError("The given sample ID doesn't exist")

    else:
        raise request_HTTPError("Error: "+response.status_code+ " " + response.reason)

    return result


def sendProjects(session, projectDict):
    #validate projectDict

    #{"name":["You must provide a project name."],"label":["You must provide a label."]} - label?

    if projectDict.has_key("name"):
        url=baseURL+"projects"
        jsonObj=json.dumps(projectDict)
        headers = {'headers': {'Content-Type':'application/json'}}

        response =session.post(url,jsonObj, **headers)

        if response.status_code==httplib.CREATED:
            print response.text
        else:
            raise ProjectError("Error: " + str(response.status_code) + " "+ response.text)

    else:
        raise ProjectError("Missing project name. A project requires 'name' as one of its keys")



def sendSequenceFile(session, projectID, sampleID, pfList):
    url=baseURL+"projects/"+projectID+"/samples/"+sampleID+"/sequenceFiles"

    headers = {'headers': {'Content-Type':'application/json'}}



#temp- will become data taken from user input
if __name__=="__main__":
    baseURL="http://localhost:8080/api/"
    username="admin"
    password="password1"

    session=createSession(baseURL, username, password)
    #projectsList=getProjects(session,baseURL)
    #print len(projectsList)
    #print projectsList[0])

    
