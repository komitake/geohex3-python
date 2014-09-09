# coding: utf-8

import math

VERSION = "3.2"

H_KEY = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
H_BASE = 20037508.34
H_DEG = math.pi * (30 / 180.0)
H_K = math.tan(H_DEG)

def calcHexSize(level):
    return H_BASE / (3.0 ** (level + 3))

class Zone:
    def __init__(self, lat, lon, x, y, code):
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.code = code
    
    def getLevel(self):
        return len(self.code) - 2
    
    def getHexSize(self):
        return calcHexSize(self.getLevel())
    
    def getHexCoords(self):
        h_lat = self.lat
        h_lon = self.lon
        h_x, h_y = loc2xy(h_lon, h_lat)
        h_deg = math.tan(math.pi * (60.0 / 180.0))
        
        h_size = self.getHexSize()
        h_top = xy2loc(h_x, h_y + h_deg *  h_size)[1]
        h_btm = xy2loc(h_x, h_y - h_deg *  h_size)[1]
        
        h_l = xy2loc(h_x - 2 * h_size, h_y)[0]
        h_r = xy2loc(h_x + 2 * h_size, h_y)[0]
        h_cl = xy2loc(h_x - 1 * h_size, h_y)[0]
        h_cr = xy2loc(h_x + 1 * h_size, h_y)[0]
        return (
            (h_lat, h_l),
            (h_top, h_cl),
            (h_top, h_cr),
            (h_lat, h_r),
            (h_btm, h_cr),
            (h_btm, h_cl)
            )
    

def getZoneByLocation(lat, lon, level):
    x, y = getXYByLocation(lat, lon, level)
    zone = getZoneByXY(x, y, level)
    return zone

def getZoneByCode(code):
    x, y = getXYByCode(code)
    level = len(code) - 2
    zone = getZoneByXY(x, y, level)
    return zone

def getXYByLocation(lat, lon, level):
    h_size = calcHexSize(level)
    lon_grid, lat_grid = loc2xy(lon, lat)
    unit_x = 6 * h_size
    unit_y = 6 * h_size * H_K
    h_pos_x = (lon_grid + lat_grid / H_K) / unit_x
    h_pos_y = (lat_grid - H_K * lon_grid) / unit_y
    h_x_0 = math.floor(h_pos_x)
    h_y_0 = math.floor(h_pos_y)
    h_x_q = h_pos_x - h_x_0
    h_y_q = h_pos_y - h_y_0
    h_x = round(h_pos_x)
    h_y = round(h_pos_y)
    
    if h_y_q > -h_x_q + 1:
        if (h_y_q < 2 * h_x_q) and (h_y_q > 0.5 * h_x_q):
            h_x = h_x_0 + 1
            h_y = h_y_0 + 1
    elif h_y_q < -h_x_q + 1:
        if (h_y_q > (2 * h_x_q) -1) and (h_y_q < (0.5 * h_x_q) + 0.5):
            h_x = h_x_0
            h_y = h_y_0
    
    h_x, h_y, h_rev = adjustXY(h_x, h_y, level)
    return (h_x, h_y)

def getXYByCode(code):
    level = len(code) - 2
    h_size = calcHexSize(level)
    unit_x = 6 * h_size
    unit_y = 6 * h_size * H_K
    h_x = 0
    h_y = 0
    h_dec9 = str(H_KEY.index(code[0]) * 30 + H_KEY.index(code[1])) + code[2:]
    if h_dec9[0] in "15" and h_dec9[1] not in "125" and h_dec9[2] not in "125":
        if h_dec9[0] == "5":
            h_dec9 = "7" + h_dec9[1:]
        elif h_dec9[0] == "1":
            h_dec9 = "3" + h_dec9[1:]
    h_dec9 = "0" * (level + 2 - len(h_dec9)) + h_dec9
    h_dec3 = ""
    for dec9s in h_dec9:
        dec9i = int(dec9s)
        h_dec3 += "012"[dec9i//3] + "012"[dec9i%3]
    
    h_decx = h_dec3[0::2]
    h_decy = h_dec3[1::2]
    
    for i in range(level + 3):
        h_pow = 3 ** (level + 2 - i)
        if h_decx[i] == "0":
            h_x -= h_pow
        elif h_decx[i] == "2":
            h_x += h_pow
        if h_decy[i] == "0":
            h_y -= h_pow
        elif h_decy[i] == "2":
            h_y += h_pow
    
    h_x, h_y, l_rev = adjustXY(h_x, h_y, level)
    return (h_x, h_y)

def getZoneByXY(x, y, level):
    h_size = calcHexSize(level)
    h_x, h_y = x, y
    
    unit_x = 6 * h_size
    unit_y = 6 * h_size * H_K
    
    h_lat = (H_K * h_x * unit_x + h_y * unit_y) / 2.0
    h_lon = (h_lat - h_y * unit_y) / H_K
    
    z_loc_x, z_loc_y = xy2loc(h_lon, h_lat)
    
    max_hsteps = 3 ** (level + 2)
    hsteps = abs(h_x - h_y)
    
    if hsteps == max_hsteps:
        if h_x > h_y:
            h_x, h_y = h_y, h_x
        z_loc_x = -180
    
    h_code = ""
    code3_x = []
    code3_y = []
    mod_x, mod_y = h_x, h_y
    for i in range(level + 3):
        h_pow = 3 ** (level + 2 - i)
        if mod_x >= math.ceil(h_pow / 2.0):
            code3_x.append(2)
            mod_x -= h_pow
        elif mod_x <= -math.ceil(h_pow / 2.0):
            code3_x.append(0)
            mod_x += h_pow
        else:
            code3_x.append(1)
        if mod_y >= math.ceil(h_pow / 2.0):
            code3_y.append(2)
            mod_y -= h_pow
        elif mod_y <= -math.ceil(h_pow / 2.0):
            code3_y.append(0)
            mod_y += h_pow
        else:
            code3_y.append(1)
    if i == 2 and (z_loc_x == -180 or z_loc_x >= 0):
        if code3_x[0] == 2 and code3_y[0] == 1 and code3_x[1] == code3_y[1] and code3_x[2] == code3_y[2]:
            code3_x[0] = 1
            code3_y[0] = 2
        elif code3_x[0] == 1 and code3_y[0] == 0 and  code3_x[1] == code3_y[1] and code3_x[2] == code3_y[2]:
            code3_x[0] = 0
            code3_y[0] = 1
    
    for i in range(len(code3_x)):
        code3 = str(code3_x[i]) + str(code3_y[i])
        code9 = str(int(code3, 3))
        h_code += code9
    
    h_2 = h_code[3:]
    h_1 = h_code[0:3]
    h_a1 = int(h_1) // 30
    h_a2 = int(h_1) % 30
    h_code = H_KEY[h_a1] + H_KEY[h_a2] + h_2
    
    return Zone(z_loc_y, z_loc_x, x, y, h_code)

def adjustXY(x, y, level):
    h_x = x
    h_y = y
    rev = 0
    max_hsteps = 3 ** (level + 2)
    hsteps = abs(h_x - h_y)
    if hsteps == max_hsteps and x > y:
        h_x, h_y = h_y, h_x
        rev = 1
    elif hsteps > max_hsteps:
        dif = hsteps - max_hsteps
        dif_x = dif // 2
        dif_y = dif - dif_x
        if x > y:
            edge_x = h_x - dif_x
            edge_y = h_y + dif_y
            edge_x, edge_y = edge_y, edge_x
            h_x = edge_x + dif_x
            h_y = edge_y - dif_y
        elif y > x:
            edge_x = h_x + dif_x
            edge_y = h_y - dif_y
            edge_x, edge_y = edge_y, edge_x
            h_x = edge_x - dif_x
            h_y = edge_y + dif_y
    return (h_x, h_y, rev)

def loc2xy(lon, lat):
    x = lon * H_BASE / 180.0
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
    y *= H_BASE / 180.0
    return (x, y)

def xy2loc(x, y):
    lon = (x / H_BASE) * 180.0
    lat = (y / H_BASE) * 180.0
    lat = 180 / math.pi * (2.0 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return (lon, lat)
