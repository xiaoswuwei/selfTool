#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sklearn.naive_bayes import MultinomialNB,GaussianNB,BernoulliNB,ComplementNB
from sklearn.externals import joblib
from sklearn.cluster import KMeans,MiniBatchKMeans
from selfTool import file,data
import decimal
from scipy.stats import pearsonr,spearmanr,kendalltau
import numpy as np

"""
class DecimalEncoder(json.JSONEncoder):
	def default(self,o):
		if isinstance(o,decimal.Decimal):
			for i,j in enumerate(o):
				o[i] = list(j)
			return list(o)
		super(DecimalEncoder,self).default(o)
"""

class bayes(object):
	def __init__(self,data,target,algorithm="GNB"):
		self.algorithm = algorithm
		self.data = data
		self.target = target
		if algorithm=='GNB':
			self.model = GaussianNB()
		elif algorithm=='MNB':
			self.model = MultinomialNB()
		elif algorithm=='BNB':
			self.model = BernoulliNB()
		else:
			self.model = ComplementNB()

		self.model.fit(data,target)

	def save_model(self,path):
		joblib.dump(self.model,path)

	def load_model(self,path):
		self.model = joblib.load(path)

	def predict(self,x):
		res = self.model.predict(x)
		return res


#层次聚类树,[9,10,5]
class Layer_kmeans(object):
	def __init__(self,cluster=[]):
		self.MODEL = "Layer_kmeans"
		self._cluster = cluster
		self._clust_len = 0
		self._cluster_tree = {
			"position":'root',
			"festival":[],
			"center_point":None
		}

	@property
	def result(self):
		return self._cluster_tree

	#arguments:the target data(mast be 2d),words with data,先分为9个类存为文件
	def tencent(self,data,words,clusters=[5]):
		_kmeans_tree = {
			"position":"root",
			"center_point":[],
			"festival":{}
		}

		class_data = {}

		one = clusters.pop(0)
		km = KMeans(init="k-means++",n_clusters=one)
		km.fit_predict(data)
		points = []

		for j,i in enumerate(km.cluster_centers_):
			key = 'file'+str(j)
			points.append(list(i))
			class_data[key] = {}
		_kmeans_tree['center_point'] = points

		#将所有数据按类分开,存成字典
		for a,b in enumerate(km.labels_):
			key2 = 'file' + str(b)
			class_data[key2][words[a]] = data[a]

		#各类存到不同的文件
		for idx in range(one):
			key1 = 'file' + str(idx)
			save_path = 'data/tree' + str(idx) + '.json'
			_kmeans_tree['festival'][key1] = save_path 
			file.op_file(file_path=save_path,data=class_data[key1],model='json',method='save')
			#保存后删除
			del class_data[key1]
		#存储根节点查找文件
		file.op_file(file_path='data/root.json',data=_kmeans_tree,model='json',method='save')
	
	#处理腾讯的9个词向量文件
	def take9_file(self,root_path):
		file_tree = {
			"tree0":0,
			"tree1":0,
			"tree2":0,
			"tree3":0,
			"tree4":0,
			"tree5":0,
			"tree6":0,
			"tree7":0,
			"tree8":0
		} 
		for f in range(3,9):
			key = 'tree' + str(f)

			f_p = 'data/tencent/tree' + str(f) +'.json'
			file_tree[key] = file.op_file(f_p,method='read')

			vals = list(file_tree[key].values())
			ks = list(file_tree[key].keys())

			sp = 'data/tencent/tc_tree' + str(f) + '.json'
			self.cluster(vals,ks,sp)
			del file_tree[key]
			del self._cluster_tree

			self._cluster_tree = {
					"position":'root',
					"festival":[],
					"center_point":None
				}
			print(ord)


	#这里开以开多线程操作,info with data(如果内存够用的话)
	def cluster(self,data,keys,save_path):
		self._clust_len = len(self._cluster) - 1
		self._basic_cluster(data,keys,self._cluster_tree,0)

		file.op_file(file_path=save_path,data=self._cluster_tree,model='json',method='save')
		"""
		***存储的数据结构：
		*{
		*	center_point:[],
		*	position:0,
		*	festival:[{
		*		center_point:[],
		*		position:last,
		*		festival:[{word1:val,word2:val,...}]
		*	},{...},...]
		*}
		"""
 
	#参数：聚类数据、类数，当前层位置
	def _basic_cluster(self,data,keys,tree_obj,position=0):

		if position=='last':
			n_clusters = self._cluster[self._clust_len]
		else:
			n_clusters = self._cluster[position]

		dts = []
		for v in range(n_clusters):
			dts.append({})

		#当样本data长度小于n_clusters时
		n_clusters = len(data) if len(data)<n_clusters else n_clusters

		km = KMeans(init="k-means++",n_clusters=n_clusters)
		km.fit_predict(data)

		#将得到的各类别分开
		for i,j in enumerate(km.labels_): 
			dts[j][keys[i]] = data[i]

		#利用对象传参是按引用传递的方法来完善整颗树。得到的点
		center_data = []
		for cd in km.cluster_centers_:
			center_data.append(list(cd))

		tree_obj['center_point'] = center_data
		tree_obj['position'] = position

		if position!='last':
			for i,g in enumerate(dts):
				tree_obj['festival'].append({
						"center_point":0,
						"festival":[],
						"position":''
					})
				pt = 'last' if position+1==self._clust_len else (position + 1)
				next_keys = list(g.keys())
				next_values = list(g.values())
				self._basic_cluster(next_values,next_keys,tree_obj['festival'][i],pt)
		else:
			#至此一个循环完成
			tree_obj['festival'] = dts

	#从腾讯词向量中查找相似
	def search_tencent(self,dts,root_path,branchs=2,candidate=1,distance=3):
		root = file.op_file(root_path,method='read')
		dist = {}
		for idx,i in enumerate(root['center_point']):
			val = data.point_distance(dts,i)
			dist[round(val,3)] = idx

		keys = list(dist.keys())
		keys.sort()
		sel_point = len(root['center_point']) if len(root['center_point'])<branchs[0] else branchs[0]
		branchs.pop(0)

		all_res = []
		for j in range(sel_point):
			k = 'file' + str(dist[keys[j]])
			path = root['festival'][k]
			sr = self.similirity(dts,path,branchs,candidate,distance)
			all_res.extend(sr)

		boult = [g for g in sorted(all_res,key=lambda k:k[0],reverse=False)]
		save_len = candidate if candidate<len(boult) else len(boult)
		return boult[0:save_len]

	#查找相似数据，data,file,查找最近的两个分支，最多保留5个值,最大匹配距离，超过该值则剔除
	def similirity(self,data,file_path,branchs=[2,2],candidate=3,distance=15):

		self._max_dist = distance
		self._search_branch = branchs
		self._search_result = []

		result = file.op_file(file_path,model='json',method='read')
		self.search_tree(data,result)

		sr = [c for c in sorted(self._search_result,key=lambda k:k[0],reverse=False)]
		save_len = candidate if candidate<len(sr) else len(sr)
		return sr[0:save_len]


	def search_tree(self,dts,tree):
		center_distance = {}
		#与各质心点计算距离，排序，选择点个数。
		for idx,i in enumerate(tree['center_point']):
			dist = data.point_distance(dts,i)
			#距离为键，索引为值
			center_distance[round(dist,3)] = idx

		keys = list(center_distance.keys())
		keys.sort()

		pdx1 = tree['position'] if tree['position']!='last' else (len(self._search_branch)-1) 
		sel_point = len(tree['center_point']) if len(tree['center_point'])<self._search_branch[pdx1] else self._search_branch[pdx1]
 
		index_arr = []
		for j in range(sel_point):
			if keys[j]>self._max_dist:
				break
			else:
				#找到最小距离分支的索引
				index_arr.append(center_distance[keys[j]])
		#不是最后一层则向下查找		
		if tree['position']!='last':
			for m in index_arr:
				self.search_tree(dts,tree['festival'][m])
		else:
			last_festival = []
			
			#至此完成一个循环
			for n in range(sel_point):
				#每条数据是:距离、对应的数据信息
				last_festival.append(tree['festival'][index_arr[n]])
			#将最近距离的几个节点放到last_festival中
			for t in last_festival:
				dist_obj = {}
				for v in t:
					#计算每个节点中与目标的距离
					dist_obj[v] = data.point_distance(dts,t[v])
				#words key array
				sort_dist = [y[0] for y in sorted(dist_obj.items(),key=lambda s:s[1],reverse=False)]

				pdx2 = tree['position'] if tree['position']!='last' else (len(self._search_branch)-1) 

				sel_len = len(sort_dist) if len(sort_dist)<self._search_branch[pdx2] else self._search_branch[pdx2]
				#保留距离最近的几个
				sel_res = sort_dist[0:sel_len]

				for g in sel_res:
					self._search_result.append([dist_obj[g],{g:t[g]}])



class AnalysisCalc(object):
	def _pearson(self,x,y)->'皮尔逊相关系数':
		_a = pearsonr(x,y)
		return _a

	def _spearman(self,x,y)->'斯皮尔曼系数':
		_p = spearmanr(x,y,axis=0,nan_policy='omit')
		return _p
	
	def _kendal(self,x,y)->'肯德尔系数':
		_k = kendalltau(x,y,nan_policy='omit')
		return _k
	
	def _cov(self,x,y):
		_scalx = np.max(x) - np.mean(x)
		_scaly = np.max(y) - np.mean(y)
		# 映射到-1～1
		return np.cov(x,y) / (_scalx * _scaly)
	
	def _mutualInfo(self,x,y)->'互信息计算':
		_counter_x = dict()
		_counter_y = dict()
		_counter_xy = dict()

		# 统计各项值出现的频率
		def _counter(key,obj):
			if key in obj:
				obj[key] += 1
			else:
				obj[key] = 1
		
		for a,b in zip(x,y):
			_key1 = str(a)
			_key2 = str(b)
			_key1_and_2 = _key1 + _key2

			_counter(_key1,_counter_x)
			_counter(_key1_and_2,_counter_xy)
			_counter(_key2,_counter_y)	
		
		_res = 0
		for v in _counter_xy:
			ks = v.split('-')

			_pxy = _counter_xy[v]
			_px = _counter_x[ks[0]]
			_py = _counter_y[ks[1]]

			_res += _pxy * np.log2(_pxy / (_px * _py))
		
		return _res
