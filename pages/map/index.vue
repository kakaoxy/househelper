<template>
  <view class="map-container">
    <map
    id="myMap"
    class="map"
    :latitude="mapCenter.latitude"
    :longitude="mapCenter.longitude"
    :scale="mapScale"
    :markers="markers"
    :polygons="polygons"
    show-location="false"
    show-label
    @regionchange="onRegionChange"
    @tap="onMapTap"
    ></map>
    
    <view class="controls">
      <view class="control-item" @tap="zoomIn">
        <text class="control-icon">+</text>
      </view>
      <view class="control-item" @tap="zoomOut">
        <text class="control-icon">-</text>
      </view>
      <view class="control-item" @tap="resetMap">
        <text class="control-icon">⟳</text>
      </view>
    </view>
    
    <view class="info-panel" v-if="selectedArea">
      <view class="panel-header">
        <text class="area-name">{{ selectedArea.properties['属性1'] }}</text>
        <text class="close-btn" @tap="closePanel">×</text>
      </view>
      <view class="panel-content">
        <view class="info-item">
          <text class="info-label">房源数量:</text>
          <text class="info-value">{{ selectedArea.properties['属性2'] }}套</text>
        </view>
        <view class="info-item">
          <text class="info-label">是否热门:</text>
          <text class="info-value">{{ selectedArea.properties['属性3'] ? '是' : '否' }}</text>
        </view>
        <button class="view-houses-btn" @tap="viewHouses(selectedArea)">查看房源</button>
      </view>
    </view>
  </view>
</template>

<script>
// import areaData from '@/static/data/areas.js'

export default {
  data() {
    return {
      mapCenter: {
        latitude: 30.25,
        longitude: 120.17
      },
      mapScale: 12,
      markers: [],
      polygons: [],
      geoJson: null,
      selectedArea: null
    }
  },
  onLoad() {
    this.loadGeoJson()
  },
  methods: {
    async loadGeoJson() {
      try {
        // 修改请求URL，移除文件扩展名
        const response = await uni.request({
          url: 'http://localhost:8000/api/v1/geojson/hangzhoushangquan.geojson',
          method: 'GET'
        });
        
        if (response.statusCode === 200) {
          this.geoJson = response.data;  // 直接使用返回的数据，不需要 .data
          this.renderGeoJson();
        } else {
          throw new Error('获取数据失败');
        }
      } catch (error) {
        console.error('加载GeoJSON数据失败:', error);
        uni.showToast({
          title: '加载地图数据失败',
          icon: 'none'
        });
        uni.showToast({
          title: '加载地图数据失败',
          icon: 'none'
        });
        // 添加备用方案：使用本地数据
        // this.geoJson = areaData;
        this.renderGeoJson();
      }
    },
    renderGeoJson() {
      if (!this.geoJson || !this.geoJson.features) return
      
      const polygons = []
      const markers = [] // 添加标记数组用于显示文字
      
      this.geoJson.features.forEach((feature, index) => {
        if (feature.geometry.type === 'Polygon') {
          // 转换坐标格式
          const points = feature.geometry.coordinates[0].map(coord => {
            return {
              longitude: coord[0],
              latitude: coord[1]
            }
          })
          
          // 计算多边形中心点
          const center = this.calculatePolygonCenter(points)
          
          // 创建多边形 - 调整透明度到15%
          polygons.push({
            points: points,
            strokeWidth: 2,
            strokeColor: '#3366CC',
            fillColor: 'rgba(51, 153, 255, 0.8)',
            zIndex: 1,
            id: index
          })
          
          // 添加文本标记
          markers.push({
            id: index,
            latitude: center.latitude,
            longitude: center.longitude,
            width: 0,
            height: 0,
            anchor: {x: 0.5, y: 0.5},
            // iconPath: '/static/transparent.png',
            callout: {
              content: feature.properties['属性1'],
              color: '#333333',
              fontSize: 14,
              borderRadius: 4,
              bgColor: 'rgba(255, 255, 255, 0.8)',
              padding: 5,
              display: 'ALWAYS'
            }
          })
        }
      })
      
      this.polygons = polygons
      this.markers = markers // 设置标记
    },
    // 添加计算多边形中心点的方法
    calculatePolygonCenter(points) {
      let sumLng = 0
      let sumLat = 0
      points.forEach(point => {
        sumLng += point.longitude
        sumLat += point.latitude
      })
      return {
        longitude: sumLng / points.length,
        latitude: sumLat / points.length
      }
    },
    onMapTap(e) {
      // 检查点击是否在多边形内
      const { latitude, longitude } = e.detail
      
      this.geoJson.features.forEach((feature, index) => {
        if (feature.geometry.type === 'Polygon') {
          const isInside = this.isPointInPolygon(
            { latitude, longitude },
            feature.geometry.coordinates[0].map(coord => ({
              longitude: coord[0],
              latitude: coord[1]
            }))
          )
          
          if (isInside) {
            this.selectedArea = feature
            return
          }
        }
      })
    },
    isPointInPolygon(point, polygon) {
      // 射线法判断点是否在多边形内
      let inside = false
      const x = point.longitude
      const y = point.latitude
      
      for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const xi = polygon[i].longitude
        const yi = polygon[i].latitude
        const xj = polygon[j].longitude
        const yj = polygon[j].latitude
        
        const intersect = ((yi > y) !== (yj > y)) &&
          (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
        if (intersect) inside = !inside
      }
      
      return inside
    },
    zoomIn() {
      if (this.mapScale < 20) {
        this.mapScale++
      }
    },
    zoomOut() {
      if (this.mapScale > 5) {
        this.mapScale--
      }
    },
    resetMap() {
      this.mapCenter = {
        latitude: 30.25,
        longitude: 120.17
      }
      this.mapScale = 12
    },
    onRegionChange(e) {
      // 地图区域变化事件
      console.log('地图区域变化', e)
    },
    closePanel() {
      this.selectedArea = null
    },
    viewHouses(area) {
      uni.showToast({
        title: `查看${area.properties['属性1']}的房源`,
        icon: 'none'
      })
      // 这里可以跳转到房源列表页面
      // uni.navigateTo({
      //   url: `/pages/houses/list?area=${encodeURIComponent(area.properties['属性1'])}`
      // })
    }
  }
}
</script>

<style>
.map-container {
  position: relative;
  width: 100%;
  height: 100vh;
}

.map {
  width: 100%;
  height: 100%;
}

.controls {
  position: absolute;
  right: 32rpx;
  bottom: 120rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.control-item {
  width: 80rpx;
  height: 80rpx;
  background-color: #FFFFFF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

.control-icon {
  font-size: 40rpx;
  color: #007AFF;
}

.info-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #FFFFFF;
  border-radius: 24rpx 24rpx 0 0;
  padding: 32rpx;
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.05);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.area-name {
  font-size: 36rpx;
  font-weight: 600;
  color: #1C1C1E;
}

.close-btn {
  font-size: 40rpx;
  color: #8E8E93;
  padding: 8rpx;
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 28rpx;
  color: #8E8E93;
}

.info-value {
  font-size: 28rpx;
  color: #1C1C1E;
  font-weight: 500;
}

.view-houses-btn {
  margin-top: 24rpx;
  background-color: #007AFF;
  color: #FFFFFF;
  font-size: 28rpx;
  padding: 20rpx;
  border-radius: 12rpx;
  text-align: center;
}
</style>