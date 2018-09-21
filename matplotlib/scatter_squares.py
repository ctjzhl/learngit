#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import matplotlib.pyplot as plt 

x_values = list(range(1,1001))
y_values = [x**2 for x in x_values]
#edgecolor='none'：删除数据点的轮廓
plt.scatter(x_values,y_values,edgecolor='none', s=40,c=y_values,cmap=plt.cm.Blues)

plt.title('Squares Number',fontsize = 24)
plt.xlabel('Value',fontsize=14)
plt.ylabel('Squares of Value',fontsize=14)

plt.tick_params(axis='both',which='major',labelsize=14)

plt.axis([0,1100,0,1100000])

#plt.savefig('squares_plot.png',bbox_inches='tight')
plt.show()