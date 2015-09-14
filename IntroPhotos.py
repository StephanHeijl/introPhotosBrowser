# Downloads and aranges all intro photo's by color

import requests, re, shutil, os, collections, colorsys, pprint, numpy, json
from PIL import Image, ImageFilter
import cv2

def downloadImage(start, end):
	galleryUrl = "http://reactievat.nl/intro-2015-2/nggallery/page/%s"
	imgdir = "introPhotos"
	for i in range(start,end+1):
		print "Page %s" % i
		url = galleryUrl % i
		r = requests.get(url)
		images = re.findall("href=\"(.+\.JPG)\"", r.content)
	
		for im in images:
			print im
			imr = requests.get(im, stream=True)
			print imr.status_code
			with open(os.path.join(imgdir, im.split("/")[-1]), "wb") as imd:
				imd.write(imr.content)
							
def reduceColorDepth(color, by=32):
	return (color[0]/by, color[1]/by, color[2]/by)
				
def increaseColorDepth(color, by=32):
	return (color[0]*by, color[1]*by, color[2]*by)		
	
def createHTMLPage(colors, image):
	colorBoxes = ""
	for color in colors:
		if color[1] is not None:
			colorBoxes += "<div style='padding: 10px; background: rgb(%s,%s,%s); margin: 5px; display:inline-block; color: white; text-shadow: 0px 0px 5px black;'>" % color[0]
			colorBoxes += color[1]
			colorBoxes += "</div>"
		
	
	boilerplate = """
		<html><head><title>{image}</title></head>
			<body> 
			{colors}<br/></hr>
			<img src="../{image}">  </body>
		</html>		
	""".format(colors=colorBoxes, image=image)
	
	return boilerplate
	
def getAverageColor(colors):
	r,g,b = 0.0,0.0,0.0
	for color in colors:
		r += color[0]
		g += color[1]
		b += color[2]
	return (int(r/len(colors)), int(g/len(colors)), int(b/len(colors)))

groupColors = {
	(0,0,0): "Reactievat/Team Zwart",
	(192,192,192): "Team Wit/Grijs",
	(0,138,117): "Team Groen",
	(117,181,202): "Team Turquoise",
	(0,53,138): "Team Blauw",
	(224,96,149): "Team Roze",
	(213,181,106): "Team Geel",
	(170,117,0): "Team Oranje",
	(85,42,117): "Team Paars/Violet",
	(128,170,117): "Team lichtgroen",
	(254,0,0): "Team Rood"
}

	
def getMatchingGroupColor(color):
	lowest = 80
	lowestGroupName = None
	for c,groupName in groupColors.items():
		distance = numpy.linalg.norm(numpy.array(c)-numpy.array(color))
		if distance < lowest:
			lowestGroupName = groupName
			lowest = distance
			
	return lowestGroupName
	
	
def getMostProminentColorForBlock(image, x1, y1, x2, y2):
	cropped = image.crop((int(x1), int(y1), int(x2), int(y2)))
	data = cropped.getdata()
	
	colors = collections.defaultdict(int)
	for d in data:
		colors[reduceColorDepth(d)]+=1
	
	prominentColors = sorted(colors.iteritems(),key=lambda (k,v): v,reverse=True)[:3]
	return getAverageColor([ increaseColorDepth(c[0]) for c in prominentColors ])
				
def getColorsInImage(image):
	im = cv2.imread(image)
	pilImg = Image.open(image)	
	cascPath = "haarcascade_frontalface_default.xml"
	gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
	
	faceCascade = cv2.CascadeClassifier(cascPath)
	
	faces = faceCascade.detectMultiScale(
		gray,
		scaleFactor=1.1,
		minNeighbors=5,
		minSize=(30, 30),
		flags = cv2.cv.CV_HAAR_SCALE_IMAGE
	)
	
	colors = []
	if len(faces) == 0:
		return
		
	for (x, y, w, h) in faces:
		color = getMostProminentColorForBlock(pilImg, x, y+(h*1.2), x+w, y+(h*2.2))
		team = getMatchingGroupColor(color)
		if team is not None:
			colors.append( (color,team)  )
	
	if len(colors) == 0:
		return 
	
	data = {
		"image": os.path.basename(image),
		"colors": colors, 
		"teams": list(set([c[1] for c in colors]))
	}
	
	return data
	
	#with open( os.path.join("introPhotosResults", os.path.basename(image) ) + ".htm", "w" ) as output:
	#	output.write( createHTMLPage( colors, image ) )
	
jsonData = []
for i in os.listdir("introPhotos"):
	d = getColorsInImage(os.path.join("introPhotos", i))
	if d is not None:
		jsonData.append( d )
	
print "var introPhotos = "+json.dumps(jsonData)
