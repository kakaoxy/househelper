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

		<!-- 手机号授权弹窗 -->
		<!-- <view class="auth-modal" v-if="showAuthModal">
			<view class="auth-content">
				<view class="auth-title">需要授权</view>
				<view class="auth-desc">查看成交日历需要授权手机号</view>
				<button class="auth-btn" open-type="getPhoneNumber" @getphonenumber="handleGetPhoneNumber">授权手机号</button>
				<view class="auth-cancel" @tap="cancelAuth">取消</view>
			</view>
		</view> -->
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
				},
				{
					name: '成交日历',
					icon: '/static/icons/calendar.png',
					path: '/pages/calendar/index'
				},
				{
					name: '选房地图',
					icon: '/static/icons/map.png',
					path: '/pages/map/index'
				}
			],
			showAuthModal: false,
			pendingPath: ''
		}
	},
	methods: {
		async handleClick(path) {
			// 检查是否是成交日历页面
			/* if (path === '/pages/calendar/index') {
				// 检查是否已授权手机号
				try {
					const phoneNumber = uni.getStorageSync('userPhoneNumber')
					if (!phoneNumber) {
						// 显示授权弹窗
						this.pendingPath = path
						this.showAuthModal = true
						return
					}
				} catch (e) {
					console.error('获取授权状态失败:', e)
				}
			} */
			
			// 正常导航
			uni.navigateTo({
				url: path
			})
		},
		async handleGetPhoneNumber(e) {
			if (e.detail.code) {
				try {
					// 这里需要调用后端接口获取手机号
					// const res = await this.getPhoneNumber(e.detail.code)
					// const phoneNumber = res.phoneNumber
					
					// 临时使用随机号码作为示例
					const phoneNumber = '1' + Math.random().toString().slice(2, 13)
					
					// 保存手机号
					uni.setStorageSync('userPhoneNumber', phoneNumber)
					
					// 关闭弹窗
					this.showAuthModal = false
					
					// 继续导航
					if (this.pendingPath) {
						uni.navigateTo({
							url: this.pendingPath
						})
						this.pendingPath = ''
					}
				} catch (err) {
					console.error('获取手机号失败:', err)
					uni.showToast({
						title: '获取手机号失败',
						icon: 'none'
					})
				}
			} else {
				uni.showToast({
					title: '您取消了授权',
					icon: 'none'
				})
			}
		},
		cancelAuth() {
			this.showAuthModal = false
			this.pendingPath = ''
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
	font-size: 28rpx;
	color: #1C1C1E;
	font-weight: 500;
}

/* 授权弹窗样式 */
.auth-modal {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 999;
}

.auth-content {
	background-color: #FFFFFF;
	border-radius: 20rpx;
	padding: 40rpx;
	width: 80%;
	max-width: 600rpx;
}

.auth-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #1C1C1E;
	text-align: center;
	margin-bottom: 16rpx;
}

.auth-desc {
	font-size: 28rpx;
	color: #8E8E93;
	text-align: center;
	margin-bottom: 32rpx;
}

.auth-btn {
	background-color: #007AFF;
	color: #FFFFFF;
	font-size: 28rpx;
	padding: 20rpx;
	border-radius: 12rpx;
	text-align: center;
	margin-bottom: 16rpx;
}

.auth-cancel {
	font-size: 28rpx;
	color: #8E8E93;
	text-align: center;
}
</style>
