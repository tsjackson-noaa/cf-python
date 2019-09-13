import cf

q, t=cf.read('/home/david/cfdm/docs/_downloads/file.nc')

a=t.copy()
x= a.dim('T') 
x += 31

b=a.copy()
x= b.dim('T') 
x += 28

c = cf.aggregate([a, b], info=0)
print (c[0])
print ('T', repr(t))
d = cf.aggregate([c, t], info=2)
print (d)
print (d[0])
