<template>
	<view class="content">
		<view class="header">
			<!-- <text class="header-title">房产助手</text> -->
		</view>
		<view class="grid-container">
			<view class="grid-item" v-for="(item, index) in menuList" :key="index" @click="handleClick(item.path)">
				<view class="icon-wrapper">
					<image class="grid-icon" :src="item.icon" mode="aspectFit"></image>
				</view>
				<text class="grid-text">{{item.name}}</text>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				menuList: [
					{
						name: '房贷计算器',
						icon: '/static/icons/calculator.png',
						path: '/pages/calculator/index'
					}
					// {
					// 	name: '地铁线路图',
					// 	icon: '/static/icons/subway.png',
					// 	path: '/pages/subway/index'
					// },
					// {
					// 	name: '电子地图',
					// 	icon: '/static/icons/map.png',
					// 	path: '/pages/map/index'
					// },
					// {
					// 	name: '新房优缺点',
					// 	icon: '/static/icons/house.png',
					// 	path: '/pages/house-analysis/index'
					// },
					// {
					// 	name: '新房房价图',
					// 	icon: '/static/icons/price.png',
					// 	path: '/pages/price-map/index'
					// },
					// {
					// 	name: '楼盘全景图',
					// 	icon: '/static/icons/panorama.png',
					// 	path: '/pages/panorama/index'
					// }
				]
			}
		},
		methods: {
			handleClick(path) {
				uni.navigateTo({
					url: path
				})
			}
		}
	}
</script>

<style>
	.content {
		padding: 0;
		background-color: #F2F2F7;
		min-height: 100vh;
	}

	.header {
		padding: 88rpx 32rpx 24rpx;
		background-color: #FFFFFF;
	}

	.header-title {
		font-size: 34px;
		font-weight: 700;
		color: #000000;
		line-height: 41px;
		letter-spacing: 0.374px;
	}

	.grid-container {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 16rpx;
		padding: 16rpx;
		margin-top: 16rpx;
	}

	.grid-item {
		background-color: #FFFFFF;
		border-radius: 16rpx;
		padding: 32rpx;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
		transition: all 0.2s ease;
	}

	.grid-item:active {
		transform: scale(0.98);
		background-color: #F2F2F7;
	}

	.icon-wrapper {
		background-color: #F2F2F7;
		border-radius: 16rpx;
		width: 108rpx;
		height: 108rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 16rpx;
	}

	.grid-icon {
		width: 56rpx;
		height: 56rpx;
	}

	.grid-text {
		font-size: 32rpx;
		color: #000000;
		font-weight: 500;
		letter-spacing: 0.374px;
	}
</style>
