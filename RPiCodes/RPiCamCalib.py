import picamera, picamera.array, time


def calibrate():
	rgbavg = 100
	counter = 1
	tog1 = 2
	tog2 = 2
	
	with picamera.PiCamera() as cam:
		cam.resolution = (100,60)
		cam.start_preview()
		time.sleep(1)
		cam.iso = 800
		cam.framerate = 30
		gains = cam.awb_gains
		cam.awb_mode = "off"
		cam.awb_gains = gains
		bright = 70
		con = 70
		cam.contrast = con
		cam.brightness = bright
		bvar = 0
		cvar = 0
		gmax = 100
		scord = 3
		mcord = 3
	#	cam.capture('precalib.bmp')
		with picamera.array.PiRGBArray(cam) as output:
			while rgbavg > 12 or gmax > 150:
				if not tog1%2:
					if not tog2%2:
						bvar += 5
						cam.brightness = bright + bvar
					else:
						bvar += 5
						cam.brightness = bright - bvar
				else:
					if not tog2%2:
						cvar += 5
						cam.contrast = con + cvar
						tog2 += 1
					else:
						cvar += 5
						cam.contrast = con - cvar
						tog2 += 1
				tog1 += 1
				print counter
				counter += 1
				if counter > 3:
					cam.brightness = 20
					cam.contrast = 70
					break
				brightP = cam.brightness
				conP = cam.contrast
				cam.capture(output,'rgb',use_video_port=True)
				img = output.array
				output.truncate(0)
				rtot, gtot, btot, gmax = 0, 0, 0, 0
				ysize,xsize = cam.resolution
				for s in range(xsize/2):
					s *= 2
					for m in range(ysize/2):
						m *= 2
						r,g,b = img[s, m]
						rtot += r
						gtot += g
						btot += b
						if g > gmax:
							gmax = g
							scord = s
							mcord = m
		
				ravg = rtot/(xsize*ysize/4)/2.55
				gavg = gtot/(xsize*ysize/4)/2.55
				bavg = btot/(xsize*ysize/4)/2.55
				rgbavg = (ravg + gavg + bavg)/3
		
				if (0 < scord < xsize) and (0 < mcord < ysize):
					r, g1, b = img[scord,mcord]
					r, g2, b = img[scord+1, mcord+1]
					r, g3, b = img[scord, mcord+1]
					r, g4, b = img[scord-1, mcord]
					r, g5, b = img[scord, mcord-1]
					gmaxarea = (g1 + g2 + g3 + g4 + g5)/5.
				else:
					gmaxarea = gmax
					print 'safeguard active'
		
				print rgbavg, 'percent white'
				print gmaxarea, 'g max area'
	#	cam.capture('postcalib.bmp')
		cam.stop_preview()
		cam.start_preview()	
		time.sleep(2)
		cam.stop_preview()
		return gains, bright, con

if __name__ == '__main__':
	calibrate()
		
