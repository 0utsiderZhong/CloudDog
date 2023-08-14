import {defineStore} from 'pinia'
import router from "~/plugins/router";
import {sendGetReq, sendPostReq} from "~/api/mock";
import {ref} from "vue";
let loginErr = ref("")
export default defineStore('loginStatus', {
	state() {
		return {
			result: "",
			data: {account: "sunway", password: "123456"},
		}
	},
	actions: {
		async login(data: { account: string; password: string }) {
			const res = sendPostReq({surl: "/token/", payload: data, config_obj: null}).then(
				(res) => {
					router.push({name: "/index"})
					// 使用localStorage存储token
					const storage = localStorage
					// Date.parse(...) 返回1970年1月1日UTC以来的毫秒数
					// Token 被设置为1h，因此这里加上60000 * 60毫秒
					const expiredTime = Date.now() + 60000 * 60
					storage.setItem("access.monitor", res.data.access)
					storage.setItem("refresh.monitor", res.data.refresh)
					storage.setItem("expiredTime.monitor", expiredTime.toString())
					storage.setItem("username.monitor", data.account)
					const resp =  sendGetReq({resUrl: "/user/${data.account}/"}).then((resp) => {
						storage.setItem("isSuperuser.monitor", resp.is_superuser)
						// 路由跳转，登录成功后跳转到
						const {target} = router.currentRoute.value.query
						if (target) {
							//  在vue3项目直接获取router实例即可,vue2当中是this.$router
							//  可以通过currentRoute获取路由信息
							// 使用 encodeURIComponent() 方法可以对 URI 进行编码
							// target有可能是string或LocationQueryValue ,target as string是指定类型
							router.push(decodeURIComponent(target as string))
						} else {
							router.push('/')
						}
					})
				}
			).catch(() => {
				loginErr.value = "Please check the account and password are correct!"
			})
		},
	},
	persist: true,
})