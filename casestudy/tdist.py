#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Time distribution study:
1. Histogram t1 and t2 of domestic violence over each zones
2. Histogram of t1 over each zone
3. Histogram of t2 over each zone
"""

import json
import arrow
from shapely.geometry import Polygon, Point, shape

class T(object):
    """
	T is an simple class for preprocessing raw '911callsforservice' and yielding well-prepared records in a memory-friendly way. 
	"""
    def __init__(self, fhandler, geojson=None):
        self.fhandler = fhandler
        self.polygons = self.geojson2polygons(geojson) if geojson else None

    def __iter__(self):
        """
        yield well-prepared record iteratively for each calling.
        """
        for line in self.fhandler:
            # split data string and get each field
            try:
                _id, crimecode, crimedesc, \
                date, startt, endt, \
                e911t, rect, dispt, enrt, arvt, trant, bookt, clrt, \
                lat, lng, text = line.strip().split("\t")
            except Exception as e:
                print(e)
                continue
            # preprocess into proper data format
            e911t, rect, dispt, enrt, arvt, trant, bookt, clrt = [ 
                self.tstr2arrow(startt, tstr) if tstr.strip() is not "" else None
                for tstr in [e911t, rect, dispt, enrt, arvt, trant, bookt, clrt] ]
            lat, lng = [ float(lat[:3] + "." + lat[3:]), -1 * float(lng[:3] + "." + lng[3:]) ] \
                if lat.strip() is not "" and lng.strip() is not "" else [ None, None ]
            zone  = self.zone4point((lng, lat), self.polygons) if self.polygons and lat and lng else None
            # calculate t1, t2, t3
            t1 = (dispt - e911t).seconds if dispt and e911t else None
            t2 = (arvt - dispt).seconds if arvt and dispt else None
            t3 = (clrt - arvt).seconds if clrt and arvt else None
            yield t1, t2, t3, lat, lng, zone

    @staticmethod
    def tstr2arrow(date, tstr):
        """convert time string in the format of 'hhmmss' into arrow object where 'hh' is hour, 'mm' is minutes, 'ss' is seconds."""
        date = date[:10].strip()
        tstr = tstr.strip()
        try:
            t = arrow.get(date + " " + tstr, 'YYYY-MM-DD HHmmss')
        except Exception as e:
            print(e)
            t = None
        return t
    
    @staticmethod
    def geojson2polygons(geojson):
        """parse geojson file, extract polygons and indexed by their ID."""
        polygons = {}
        with open(geojson, "r") as f:
            geo_obj = json.load(f)
            for feature in geo_obj["features"]:
                name    = feature["properties"]["ID"]
                polygon = shape(feature["geometry"])
                polygons[name] = polygon
            return polygons

    @staticmethod
    def zone4point(point, polygons):
        """get zone ID of the point."""
        for name in polygons:
            if polygons[name].contains(Point(point)):
                return name
        return None

import seaborn as sns
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib.backends.backend_pdf import PdfPages

def plot_t_distribution(tuples, savepath, t_annotation="t1"):
    tdist = defaultdict(lambda: [])
    for t, zone in tuples:
        if zone and t:
            tdist[zone].append(t)
    
    with PdfPages(savepath) as pdf:
        fig, ax = plt.subplots(1, 1)
        sns.set(color_codes=True)
        for zone in tdist:
            print(zone)
            print(len(tdist[zone]))
            print(max(tdist[zone]))
            sns.distplot(tdist[zone],
                hist=False, rug=False, ax=ax, label="zone %s (%d)" % (zone, len(tdist[zone])))
        ax.set(xlabel=t_annotation, ylabel="frequency")
        ax.set_title("distribution over zones", fontweight="bold")
        ax.legend(frameon=False)
        pdf.savefig(fig)
        

if __name__ == "__main__":
    domvio_911calls  = "/Users/woodie/Desktop/workspace/Zoning-Analysis/data/casestudy/domvio.rawdata.txt"
    all_911calls     = "/Users/woodie/Desktop/workspace/Crime-Pattern-Detection-for-APD/data/records_380k/raw_data.txt"
    apd_zone_geojson = "/Users/woodie/Desktop/workspace/Zoning-Analysis/data/apd_zone.geojson"
    with open(all_911calls, "r", encoding="utf8", errors='ignore') as f:
        tuples = [ [ t1, t2, t3, zone ] 
                   for t1, t2, t3, lat, lng, zone in T(f, geojson=apd_zone_geojson) 
                   if zone and zone != 50 ]

        t1_tuples = [ [ t1, zone ] for t1, t2, t3, zone in tuples if t1 ]
        t2_tuples = [ [ t2, zone ] for t1, t2, t3, zone in tuples if t2 ]
        t3_tuples = [ [ t3, zone ] for t1, t2, t3, zone in tuples if t3 ]

        savepath = "/Users/woodie/Desktop/workspace/Zoning-Analysis/data/casestudy/all-t1.pdf"
        plot_t_distribution(t1_tuples, savepath, t_annotation="t1")
        savepath = "/Users/woodie/Desktop/workspace/Zoning-Analysis/data/casestudy/all-t2.pdf"
        plot_t_distribution(t2_tuples, savepath, t_annotation="t2")
        savepath = "/Users/woodie/Desktop/workspace/Zoning-Analysis/data/casestudy/all-t3.pdf"
        plot_t_distribution(t3_tuples, savepath, t_annotation="t3")

        