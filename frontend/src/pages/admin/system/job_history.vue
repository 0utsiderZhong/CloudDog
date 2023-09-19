<!--Advanced Python Scheduler: Job Service-->
<template>

	<div>
		<div class="product_container">
			<div class="handle-box">
				<el-input v-model="queryConditions.project_name" placeholder="Job Name" class="handle-input mr10"></el-input>
				<el-button :icon="Search" type="primary" @click="searchJobExecutionHistory">Search</el-button>
				<el-button :icon="Refresh" type="primary" @click="getJobExecutionList" style="float: right">Refresh</el-button>
			</div>

			<el-scrollbar>
				<el-table :data="DjangoAPSchedulerJobExecutionList"
									:border="parentBorder"
									header-cell-class-name="table-header"
									scrollbar-always-on
									style="width: 100%">


					<el-table-column align="center" label="Execution ID" show-overflow-tooltip width="200px">
						<template #default="scope">
							<div style="font-weight: bold">
								{{ scope.row.id }}
							</div>
						</template>
					</el-table-column>

					<el-table-column align="center" label="Job Name" show-overflow-tooltip width="300px">
						<template #default="scope">
							<div style="font-weight: bold">
								{{ scope.row.job_id }}
							</div>
						</template>
					</el-table-column>

					<el-table-column prop="status" label="Job Status" align="center" width="180px">
						<template #default="scope">
							<div style="font-weight: bold">
								{{ scope.row.status }}
							</div>
						</template>
					</el-table-column>

					<el-table-column label="Runtime" align="center" width="100px">
						<template #default="scope">
							{{ scope.row.runtime }}
						</template>
					</el-table-column>

					<el-table-column align="center" label="Duration" show-overflow-tooltip width="150px" font-weight: bold>
						<template #default="scope" style="font-weight: bold">
							<div style="font-weight: bold">
								{{ scope.row.duration }}
							</div>
						</template>
					</el-table-column>

					<el-table-column prop="finished" align="center" label="Finished" show-overflow-tooltip width="250px">
						<template #default="scope">
							<el-tag>
								{{ scope.row.finished }}
							</el-tag>
						</template>
					</el-table-column>


					<el-table-column prop="exception" align="center" label="Exception" show-overflow-tooltip width="380px"></el-table-column>
					<el-table-column prop="traceback" align="center" label="Traceback" show-overflow-tooltip width="380px"></el-table-column>

				</el-table>
			</el-scrollbar>

			<div class="admin_pagination">
				<el-pagination
					v-model:current-page="currentPageIndex"
					v-model:page-size="pageSize"
					:page-sizes="[10, 20, 30, 50]"
					:small="small"
					:disabled="disabled"
					:background="background"
					layout="total, sizes, prev, pager, next, jumper"
					:total=pageTotal
					@size-change="handleSizeChange"
					@current-change="handlePageChange"
				/>
			</div>
		</div>

	</div>
</template>

<script setup lang="ts">
import {reactive, ref} from 'vue';
import {Refresh, Search} from '@element-plus/icons-vue';
import {ElMessage} from 'element-plus';


const parentBorder = ref(true)
const auth = ['admin', 'user']
const small = ref(false)
const background = ref(true)
const disabled = ref(false)


// The pattern of Project
interface DjangoAPSchedulerJobExecution {
	job_id: any,
	id: string,
	status: string,
	runtime: string,
	duration: string,
	finished: string,
	exception: string,
	traceback: string,
}

const DjangoAPSchedulerJobExecutionList = ref<DjangoAPSchedulerJobExecution[]>([]);
const pageTotal = ref(0);

// The conditions of search api
const queryConditions = reactive({
	project_name: "",
});

let currentPageIndex = ref(1);
let pageSize = ref(10);


// get Elastic Compute Resource list
const getJobExecutionList = () => {
	sendGetReq({
		params: {
			page_index: currentPageIndex.value,
			page_size: pageSize.value
		},
		uri: "/apsexecjob"
	}).then((res) => {
			pageTotal.value = parseInt(res.data.total)
			DjangoAPSchedulerJobExecutionList.value = res.data.data
		}
	).catch((err) => {
		ElMessage.error(err || 'Get job execution list error');
	});
}
getJobExecutionList(); // init ECR list

// search ECR by cloud_platform and project_name
const searchJobExecutionHistory = () => {
	sendGetReq({
		uri: "/apsexecjob", params: {
			job_name: queryConditions.project_name,
			page_index: currentPageIndex.value,
			page_size: pageSize.value
		}
	}).then((res) => {
			pageTotal.value = parseInt(res.data.count)
			DjangoAPSchedulerJobExecutionList.value = res.data.results
		}
	).catch((err) => {
		ElMessage.error(err || 'Search job execution history error');
	});
}

const handlePageChange = (val: number) => {
	currentPageIndex.value = val;
	getJobExecutionList();
};

const handleSizeChange = (val: number) => {
	pageSize.value = val;
	getJobExecutionList();
}


</script>

<style>
.handle-box {
	margin-bottom: 20px;
}

.handle-select {
	width: 150px;
}

.handle-input {
	width: 300px;
}


.mr10 {
	margin-right: 10px;
}

.product_container {
	padding: 30px;
	background: #fff;
	border: 1px solid #ddd;
	border-radius: 5px;
}

.el-scrollbar__bar.is-horizontal {
	height: 15px !important;
}

.el-table .warning-row {
	--el-table-tr-bg-color: var(--el-color-warning-light-9);
}

.el-table .success-row {
	--el-table-tr-bg-color: var(--el-color-success-light-9);
}

.el-popper.is-customized {
	/* Set padding to ensure the height is 32px */
	padding: 6px 12px;
	background: linear-gradient(90deg, rgb(255, 255, 255), rgb(255, 255, 255));
}

.el-popper.is-customized .el-popper__arrow::before {
	background: linear-gradient(45deg, #b2e68d, #bce689);
	right: 0;
}
</style>