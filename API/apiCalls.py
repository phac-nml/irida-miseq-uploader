import ast
import json
import httplib

import sys
sys.path.append("../")

from os import path
from requests import Request
from requests.exceptions import HTTPError as request_HTTPError
from urllib2 import Request, urlopen, URLError, HTTPError
from urlparse import urljoin

from rauth import OAuth2Service, OAuth2Session

from Model.SequenceFile import SequenceFile
from Model.Project import Project
from Model.Sample import Sample
from Model.ValidationResult import ValidationResult
from Exceptions.ProjectError import ProjectError
from Validation.offlineValidation import validateURLForm
from ConfigParser import RawConfigParser


pathToModule=path.dirname(__file__)
if len(pathToModule)==0:
    pathToModule='.'

confParser=RawConfigParser()
confParser.read(pathToModule+"/../config.conf")

clientId=confParser.get("apiCalls","clientId")
clientSecret=confParser.get("apiCalls","clientSecret")

MAX_TIMEOUT_WAIT=int(confParser.get("apiCalls","maxWaitTime"))

class ApiCalls:
    def __init__(self, clientId, clientSecret, baseURL, username, password):
        """
        Create OAuth2Session and store it

        arguments:
            clientId -- clientId for creating access token. Found in iridaUploader/config.conf
            clientSecret -- clientSecret for creating access token. Found in iridaUploader/config.conf
            baseURL -- url of the IRIDA server
            username -- username for server
            password -- password for given username

        return ApiCalls object
        """
        self.clientId=clientId
        self.clientSecret=clientSecret
        self.baseURL=baseURL
        self.username=username
        self.password=password

        self.session=self.createSession()


    def createSession(self):
        """
        create session to be re-used until expiry for get and post calls

        returns session (OAuth2Session object)
        """

        if self.baseURL[-1:]!='/':
            self.baseURL=self.baseURL+'/'

        if validateURLForm(self.baseURL):
            oauth_service=self.get_oauth_service()
            access_token=self.get_access_token(oauth_service)
            session=oauth_service.get_session(access_token)
        else:
            raise URLError(vRes.getErrors())

        return session


    def get_oauth_service(self):
        """
        get oauth service to be used to get access token


        returns oauthService
        """

        accessTokenUrl = urljoin(self.baseURL,"oauth/token")
        oauth_serv = OAuth2Service(
        client_id=clientId,
        client_secret=clientSecret,
        name="irida",
        access_token_url = accessTokenUrl,
        base_url=self.baseURL)


        return oauth_serv

    def get_access_token(self, oauth_service):
        """
        get access token to be used to get session from oauth_service

        arguments:
            oauth_service -- O2AuthService from get_oauth_service

        returns access token
        """

        params = {'data' : {'grant_type' : 'password',
            'client_id' : clientId,
            'client_secret' : clientSecret,
            'username' : self.username,
            'password' : self.password}}

        access_token =    oauth_service.get_access_token(decoder=self.decoder,**params)

        return access_token


    def decoder(self, return_dict):
        """
        safely parse given dictionary

        arguments:
            return_dict -- access token dictionary

        returns evaluated dictionary
        """

        irida_dict = ast.literal_eval(return_dict)
        return irida_dict


    def validateURLexistence(self, url, useSession=False):
        """
        tries to validate existence of given url by trying to open it.
        true if HTTP OK, false if HTTP NOT FOUND otherwise raises error containing error code and message

        arguments:
            url -- the url link to open and validate
            useSession -- if True then this uses self.session.get(url) instead of urlopen(url) to get response

        returns
            true if http response OK 200
            false if http response NOT FOUND 404
        """

        if useSession==True:
            response=self.session.get(url)

            if response.status_code==httplib.OK:
                return True
            elif response.status_code==httplib.NOT_FOUND:
                return False
            else:
                raise Exception( str(response.status_code) + response.reason)

        else:
            response = urlopen(url, timeout=MAX_TIMEOUT_WAIT)

            if response.code==httplib.OK:
                return True
            elif response.code==httplib.NOT_FOUND:
                return False
            else:
                raise Exception( str(response.code) + response.msg)


    def getLink(self, targURL, targetKey, targDict=""):
        """
        makes a call to targURL(api) expecting a json response
        tries to retrieve targetKey from response to find link to that resource
        raises exceptions if targetKey not found or targURL is invalid

        arguments:
            targURL -- URL to retrieve link from
            targetKey -- name of link (e.g projects or project/samples)
            targDict -- optional dict containing key and value to search for in targets.
            (e.g {key='identifier',value='100'} to retrieve where identifier=100 )

        returns link if it exists
        """
        retVal=None

        if self.validateURLexistence(targURL, useSession=True):
            response=self.session.get(targURL)

            if len(targDict)>0:
                resourcesList=response.json()["resource"]["resources"]
                linksList=next(resource["links"] for resource in resourcesList if resource[targDict["key"]]==targDict["value"])

            else:
                linksList=response.json()["resource"]["links"]

            retVal=next(link["href"] for link in linksList if link["rel"]==targetKey)

            if retVal==None:
                raise KeyError(targetKey+" not found in links. "+ "Available links: " + ",".join([ str(link["rel"]) for link in linksList])[:-1] )

        else:
            raise request_HTTPError("Error: " + targURL +" is not a valid URL")

        return retVal


    def getProjects(self):
        """
        API call to api/projects to get list of projects

        returns list containing projects. each project is Project object.
        """

        projectList=[]

        url=self.getLink(self.baseURL, "projects")
        response = self.session.get(url)

        result= response.json()["resource"]["resources"]
        projectList=[Project(projDict["name"], projDict["projectDescription"], projDict["identifier"]) for projDict in result]

        return projectList


    def getSamples(self, project):
        """
        API call to api/projects/projectID/samples

        arguments:
            project -- a Project object used to get projectID

        returns list of samples for the given project. each sample is a Sample object.
        """

        sampleList=[]
        projectID=project.getID()

        try:
            projUrl=self.getLink(self.baseURL, "projects")
            url=self.getLink(projUrl, "project/samples", targDict={"key":"identifier","value":projectID})


        except StopIteration:
            raise Exception("The given project ID: "+ projectID +" doesn't exist")

        response = self.session.get(url)
        result = response.json()["resource"]["resources"]
        sampleList=[Sample(sampleDict) for sampleDict in result]

        return sampleList


    def getSequenceFiles(self, project, sample):
        """
        API call to api/projects/projectID/sampleID/sequenceFiles

        arguments:
            project -- a Project object used to get projectID
            sample -- a Sample object used to get sampleID


        returns list of sequencefile dictionary for given sampleID
        """
        projectID=project.getID()
        sampleID=sample.getID()

        try:
            projUrl=self.getLink(self.baseURL, "projects")
            sampleUrl=self.getLink(projUrl, "project/samples", targDict={"key":"identifier","value":projectID})

        except StopIteration:
            raise Exception("The given project ID: "+ projectID +" doesn't exist")

        try:
            url=self.getLink(sampleUrl, "sample/sequenceFiles",targDict={"key":"sequencerSampleId","value":sampleID})
            response = self.session.get(url)

        except StopIteration:
            raise Exception("The given sample ID: "+ sampleID +" doesn't exist")

        result=response.json()["resource"]["resources"]

        return result


    def sendProjects(session, baseURL, project):
        """
        post request to send a project to IRIDA via API
        the project being sent requires a name

        arguments:
            session -- opened OAuth2Session
            baseURL -- URL of IRIDA server API
            project -- a Project object to be sent.

        returns a dictionary containing the result of post request. when post is successful the dictionary it returns will contain the same name and projectDescription that was originally sent as well as additional keys like createdDate and identifier.
        when post fails then an error will be raised so return statement is not even reached.
        """

        jsonRes=None
        if len(project.getName())>5:
            url=getLink(session, baseURL, "projects")
            jsonObj=json.dumps(project.getDict())
            headers = {'headers': {'Content-Type':'application/json'}}

            response =session.post(url,jsonObj, **headers)

            if response.status_code==httplib.CREATED:#201
                jsonRes= json.loads(response.text)
            else:
                raise ProjectError("Error: " + str(response.status_code) + " "+ response.text)

        else:
            raise ProjectError("Missing project name. A project requires a name that must be 5 or more characters.")

        return jsonRes


    def sendSamples(session, baseURL, project, samplesList):
        """
        post request to send sample(s) to the project of given projectID

        arguments:
            session -- opened OAuth2Session
            baseURL -- URL of IRIDA server API
            project -- a Project object used to get project ID
            samplesList -- list containing Sample object(s) to send
        """

        jsonRes=None
        projectID=project.getID()
        try:
            projUrl=getLink(session, baseURL, "projects")
            url=getLink(session, projUrl, "project/samples", targDict={"key":"identifier","value":projectID})
            response = session.get(url)

        except StopIteration:
            raise Exception("The given project ID: "+ projectID +" doesn't exist")

        headers = {'headers': {'Content-Type':'application/json'}}

        for sample in samplesList:
            jsonObj=json.dumps(sample.getDict())
            response =session.post(url, jsonObj, **headers)

            if response.status_code==httplib.CREATED:#201
                jsonRes= json.loads(response.text)
            else:
                raise ProjectError("Error: " + str(response.status_code) + " "+ response.text)

        return jsonRes

if __name__=="__main__":
    baseURL="http://localhost:8080/api"
    username="admin"
    password="password1"
    api=ApiCalls(clientId, clientSecret, baseURL, username, password )
    projList=api.getProjects()
    print "#Project count:", len(projList)

    projTarg=projList[3]
    sList=api.getSamples(projTarg)
    print "#Sample count:", len(sList)


    seqFiles=api.getSequenceFiles(projTarg, sList[len(sList)-1])
    print seqFiles
