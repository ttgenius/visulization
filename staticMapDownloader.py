from cStringIO import StringIO
import Image
import urllib


def download_map(latitude, longitude, outname):
    """Download  a staic map from google based on the center coordinates.
       Coords can be obtained from 'http://www.seagull.co.nz/locate.php'
    """
    url1 = "https://maps.googleapis.com/maps/api/staticmap?center={:.8f},{:.8f}&zoom=8&maptype=satellite&size=1000x1000&scale=4".format(latitude,longitude)
    buffer1 = StringIO(urllib.urlopen(url1).read())
    image = Image.open(buffer1)
    image.save('{}.png'.format(outname))


download_map(-40.24927085,164.31152344,"westsea")


#urlparams = urllib.urlencode({'center': approx_centre,
                                      #'zoom': str(zoom),
                                      #'size': '%dx%d' % (width, length),
                                      #'maptype': 'hybrid',
                                      #'sensor': 'false',
                                      #'scale': scale})
#url = "https://maps.googleapis.com/maps/api/staticmap?" + urlparams

#image1.show()
