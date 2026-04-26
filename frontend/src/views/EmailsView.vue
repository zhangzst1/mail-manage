<template>
  <div class="page-container">
    <section class="emails-hero">
      <div class="emails-hero-main page-shell">
        <div class="emails-hero-copy">
          <span class="section-kicker">Email Workspace</span>
          <h1 class="emails-hero-title">邮箱工作台</h1>
          <p class="emails-hero-description">
            把账号管理、批量收信和邮件查看整合到同一个更清晰的操作面板里，让高频动作更快找到，也更容易判断当前状态。
          </p>
        </div>

        <div class="emails-hero-actions">
          <el-button type="primary" @click="refreshEmails" :icon="Refresh" class="hero-action hero-action-dark">
            刷新列表
          </el-button>
          <el-button type="success" @click="showAddEmailDialog" :icon="Plus" class="hero-action hero-action-accent">
            添加邮箱
          </el-button>
          <el-button type="info" @click="openAllMailsDialog" :icon="Message" class="hero-action hero-action-light">
            查看全部邮件
          </el-button>
        </div>
      </div>

      <div class="emails-hero-stats">
        <article v-for="item in overviewStats" :key="item.label" class="hero-stat-card page-shell">
          <span class="hero-stat-label">{{ item.label }}</span>
          <strong class="hero-stat-value">{{ item.value }}</strong>
          <p class="hero-stat-hint">{{ item.hint }}</p>
        </article>
      </div>
    </section>

    <div class="emails-container">
      <el-card class="email-list-card shadow page-shell">
        <template #header>
          <div class="card-header flex-between">
            <div class="title-group">
              <h2 class="page-title">邮箱列表</h2>
              <p class="card-subtitle">统一查看账户、配置、最近检查时间和常用操作。</p>
            </div>
            <div class="actions flex gap-md">
              <el-button type="primary" @click="refreshEmails" :icon="Refresh" class="hover-scale">
                刷新列表
              </el-button>
              <el-button type="info" @click="openAllMailsDialog" :icon="Message" class="hover-scale">
                查看全部邮件
              </el-button>
              <el-button type="success" @click="showAddEmailDialog" :icon="Plus" class="hover-scale">
                添加邮箱
              </el-button>
            </div>
          </div>
        </template>

        <div class="toolbar flex gap-md mb-4">
          <el-button
            type="danger"
            :disabled="!hasSelectedEmails"
            @click="handleBatchDelete"
            :icon="Delete"
            class="hover-scale"
          >
            批量删除
          </el-button>
          <el-button
            type="primary"
            :disabled="!hasSelectedEmails"
            @click="handleBatchCheck"
            :icon="Download"
            class="hover-scale"
          >
            批量收信
          </el-button>
        </div>

        <el-table
          v-loading="loading"
          :data="emails"
          @selection-change="handleSelectionChange"
          style="width: 100%"
          stripe
          border
          highlight-current-row
          class="email-table"
        >
          <el-table-column
            type="selection"
            width="55"
            :selectable="row => row"
          />
          <el-table-column prop="email" label="邮箱地址" width="220" />
          <el-table-column prop="mail_type" label="邮箱类型" width="120">
            <template #default="scope">
              <el-tag
                :type="getMailTypeColor(scope.row.mail_type || 'outlook')"
                effect="plain"
                class="mail-type-tag"
              >
                {{ getMailTypeName(scope.row.mail_type || 'outlook') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="password" label="密码" width="150">
            <template #default="scope">
              <div class="password-field flex-between">
                <span class="password-text">{{ scope.row.showPassword ? scope.row.password : '******' }}</span>
                <el-button
                  type="primary"
                  link
                  :icon="scope.row.showPassword ? Hide : View"
                  @click="togglePasswordVisibility(scope.row)"
                  :loading="scope.row.passwordLoading"
                  class="password-toggle-btn"
                />
              </div>
            </template>
          </el-table-column>
          <el-table-column label="配置信息" width="200">
            <template #default="scope">
              <template v-if="scope.row.mail_type === 'imap'">
                <div class="server-info">
                  <div class="server-field">
                    <strong>服务器:</strong> {{ scope.row.server || 'N/A' }}
                  </div>
                  <div class="port-field">
                    <strong>端口:</strong> {{ scope.row.port || 'N/A' }}
                  </div>
                </div>
              </template>
              <template v-else-if="scope.row.mail_type === 'gmail'">
                <div class="config-info">
                  <div>服务器: imap.gmail.com</div>
                  <div>端口: 993</div>
                </div>
              </template>
              <template v-else-if="scope.row.mail_type === 'qq'">
                <div class="config-info">
                  <div>服务器: imap.qq.com</div>
                  <div>端口: 993</div>
                </div>
              </template>
              <template v-else>
                <div class="config-info">标准配置</div>
              </template>
            </template>
          </el-table-column>
          <el-table-column prop="last_check_time" label="最后检查时间" width="180">
            <template #default="scope">
              <span>{{ formatDate(scope.row.last_check_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="440">
            <template #default="scope">
              <div class="action-buttons flex gap-sm">
                <el-button
                  type="primary"
                  size="small"
                  :disabled="isEmailProcessing(scope.row)"
                  @click="handleCheck(scope.row)"
                  class="action-btn"
                >
                  {{ getEmailActionText(scope.row) }}
                </el-button>
                <el-button
                  type="success"
                  size="small"
                  @click="handleViewMails(scope.row)"
                  class="action-btn"
                >
                  查看邮件
                </el-button>
                <el-button
                  v-if="canUseGraph(scope.row)"
                  type="info"
                  size="small"
                  @click="openGraphMailDialog(scope.row)"
                  class="action-btn"
                >
                  Graph 邮件
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="handleDelete(scope.row)"
                  class="action-btn"
                >
                  删除
                </el-button>
                <el-button
                  type="warning"
                  size="small"
                  @click="handleEdit(scope.row)"
                  class="action-btn"
                >
                  编辑
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 添加邮箱对话框 -->
      <el-dialog
        v-model="addEmailDialogVisible"
        title="添加邮箱"
        width="600px"
        :close-on-click-modal="false"
        class="add-email-dialog"
        destroy-on-close
      >
        <el-tabs v-model="addEmailActiveTab">
          <el-tab-pane label="单个添加" name="single">
            <el-form
              ref="addEmailFormRef"
              :model="addEmailForm"
              :rules="addEmailRules"
              label-width="120px"
              class="add-email-form"
            >
              <el-form-item label="邮箱类型" prop="mail_type">
                <el-select v-model="addEmailForm.mail_type" placeholder="请选择邮箱类型" class="w-full">
                  <el-option
                    v-for="(config, type) in mailTypes"
                    :key="type"
                    :label="config.name"
                    :value="type"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="邮箱地址" prop="email">
                <el-input v-model="addEmailForm.email" placeholder="请输入邮箱地址" />
              </el-form-item>

              <el-form-item label="密码" prop="password">
                <el-input
                  v-model="addEmailForm.password"
                  type="password"
                  placeholder="请输入密码"
                  show-password
                />
              </el-form-item>

              <template v-if="addEmailForm.mail_type === 'outlook'">
                <el-form-item label="Client ID" prop="client_id">
                  <el-input v-model="addEmailForm.client_id" placeholder="请输入Client ID" />
                </el-form-item>

                <el-form-item label="Refresh Token" prop="refresh_token">
                  <el-input v-model="addEmailForm.refresh_token" placeholder="请输入Refresh Token" />
                </el-form-item>
              </template>

              <template v-if="addEmailForm.mail_type === 'imap'">
                <el-form-item label="服务器" prop="server">
                  <el-input v-model="addEmailForm.server" placeholder="请输入IMAP服务器地址" />
                </el-form-item>

                <el-form-item label="端口" prop="port">
                  <el-input-number v-model="addEmailForm.port" :min="1" :max="65535" />
                </el-form-item>

                <el-form-item label="使用SSL" prop="use_ssl">
                  <el-switch v-model="addEmailForm.use_ssl" />
                </el-form-item>
              </template>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="批量添加" name="batch">
            <p class="import-help">请按照以下格式输入邮箱信息，每行一个：<br/>邮箱地址----密码----客户端ID----刷新令牌</p>
            <el-form :model="batchImport" label-width="120px" :rules="batchImportRules" ref="batchImportFormRef">
              <el-form-item label="邮箱类型">
                <el-select v-model="batchImport.mailType" placeholder="请选择邮箱类型">
                  <el-option
                    label="Outlook/Hotmail"
                    value="outlook"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="批量数据" prop="data">
                <el-input
                  v-model="batchImport.data"
                  type="textarea"
                  :rows="10"
                  placeholder="例如: example@outlook.com----password----clientid----refreshtoken"
                />
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <template #footer>
          <span class="dialog-footer">
            <el-button @click="addEmailDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleAddOrImport" :loading="addingEmail || importing">
              确定
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 邮件列表对话框 -->
      <el-dialog
        v-model="mailListDialogVisible"
        title="邮件列表"
        width="90%"
        top="5vh"
        class="mail-list-dialog"
        destroy-on-close
      >
        <div v-if="currentEmail" class="mail-dialog-header flex-between mb-4">
          <h3 class="email-title">
            <span class="text-primary">{{ currentEmail.email }}</span> 的邮件
          </h3>
          <el-button
            type="primary"
            size="small"
            @click="handleCheck(currentEmail)"
            :disabled="isEmailProcessing(currentEmail)"
            :icon="Refresh"
            class="refresh-btn hover-scale"
          >
            刷新邮件
          </el-button>
        </div>

        <el-table
          v-loading="loadingMails"
          :data="mailRecords"
          style="width: 100%"
          stripe
          border
          max-height="60vh"
          class="mail-list-table"
        >
          <el-table-column prop="subject" label="主题" min-width="250" show-overflow-tooltip>
            <template #default="scope">
              <div class="subject-cell">
                <span>{{ scope.row.subject }}</span>
                <el-tag v-if="scope.row.has_attachments" size="small" type="success" class="attachment-tag">
                  <el-icon><Document /></el-icon> 附件
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="sender" label="发件人" min-width="200" show-overflow-tooltip />
          <el-table-column prop="received_time" label="接收时间" width="180">
            <template #default="scope">
              <span class="time-field">{{ formatDate(scope.row.received_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="scope">
              <el-button
                type="primary"
                size="small"
                @click="viewMailContent(scope.row)"
                :icon="Document"
                class="view-btn"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-dialog>

      <el-dialog
        v-model="allMailListDialogVisible"
        title="全部邮件列表"
        width="92%"
        top="4vh"
        class="mail-list-dialog"
        destroy-on-close
      >
        <div class="mail-dialog-header flex-between mb-4">
          <el-input
            v-model="allMailSearch"
            placeholder="搜索邮箱、主题、发件人或内容"
            clearable
            class="all-mail-search"
          />
          <el-button
            type="primary"
            size="small"
            @click="fetchAllMails"
            :loading="loadingAllMails"
            :icon="Refresh"
            class="refresh-btn hover-scale"
          >
            刷新邮件
          </el-button>
        </div>

        <el-table
          v-loading="loadingAllMails"
          :data="filteredAllMailRecords"
          style="width: 100%"
          stripe
          border
          max-height="65vh"
          class="mail-list-table"
        >
          <el-table-column prop="email_address" label="邮箱" min-width="220" show-overflow-tooltip />
          <el-table-column prop="subject" label="主题" min-width="260" show-overflow-tooltip>
            <template #default="scope">
              <div class="subject-cell">
                <span>{{ scope.row.subject }}</span>
                <el-tag v-if="scope.row.has_attachments" size="small" type="success" class="attachment-tag">
                  <el-icon><Document /></el-icon> 附件
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="sender" label="发件人" min-width="220" show-overflow-tooltip />
          <el-table-column prop="received_time" label="接收时间" width="180">
            <template #default="scope">
              <span class="time-field">{{ formatDate(scope.row.received_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="scope">
              <el-button
                type="primary"
                size="small"
                @click="viewMailContent(scope.row)"
                :icon="Document"
                class="view-btn"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-dialog>

      <el-dialog
        v-model="graphMailDialogVisible"
        title="Graph 邮件列表"
        width="92%"
        top="4vh"
        class="mail-list-dialog"
        destroy-on-close
      >
        <div v-if="graphEmail" class="mail-dialog-header flex-between mb-4">
          <div class="graph-mail-header">
            <h3 class="email-title">
              <span class="text-primary">{{ graphEmail.email }}</span> 的 Graph 邮件
            </h3>
            <span class="graph-mail-count">共 {{ filteredGraphMailRecords.length }} 封</span>
            <span class="graph-mail-memory">{{ graphMailMemoryHint }}</span>
          </div>
          <div class="actions flex gap-md">
            <el-input
              v-model="graphMailSearch"
              placeholder="搜索主题、发件人或内容"
              clearable
              class="all-mail-search"
            />
            <el-button
              type="primary"
              size="small"
              @click="fetchGraphMails(graphEmail, { sync: true })"
              :loading="loadingGraphMails"
              :icon="Refresh"
              class="refresh-btn hover-scale"
            >
              {{ graphMailFetchButtonText }}
            </el-button>
          </div>
        </div>

        <el-table
          v-loading="loadingGraphMails"
          :data="filteredGraphMailRecords"
          :empty-text="graphMailEmptyText"
          style="width: 100%"
          stripe
          border
          max-height="65vh"
          class="mail-list-table"
        >
          <el-table-column prop="subject" label="主题" min-width="260" show-overflow-tooltip>
            <template #default="scope">
              <div class="subject-cell">
                <span>{{ scope.row.subject }}</span>
                <el-tag v-if="scope.row.has_attachments" size="small" type="success" class="attachment-tag">
                  <el-icon><Document /></el-icon> 附件
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="sender" label="发件人" min-width="220" show-overflow-tooltip />
          <el-table-column prop="received_time" label="接收时间" width="180">
            <template #default="scope">
              <span class="time-field">{{ formatDate(scope.row.received_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="is_read" label="状态" width="90">
            <template #default="scope">
              <el-tag size="small" :type="scope.row.is_read ? 'info' : 'danger'">
                {{ scope.row.is_read ? '已读' : '未读' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="scope">
              <el-button
                type="primary"
                size="small"
                @click="viewMailContent(scope.row)"
                :icon="Document"
                class="view-btn"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-dialog>

      <!-- 邮件内容查看对话框 -->
      <el-dialog
        v-model="mailContentDialogVisible"
        :title="selectedMail ? selectedMail.subject : '邮件详情'"
        width="80%"
        top="5vh"
        class="mail-content-dialog"
      >
        <div v-if="selectedMail" class="mail-detail">
          <!-- 使用EmailContentViewer组件 -->
          <MailpeekEmailViewer
            :mail="selectedMail"
            :attachments="selectedMail.attachments || []"
            :loading-attachments="false"
          />
        </div>
      </el-dialog>

      <!-- 编辑邮箱对话框 -->
      <el-dialog
        v-model="editDialogVisible"
        title="编辑邮箱"
        width="500px"
        @close="resetEditForm"
      >
        <el-form
          ref="editFormRef"
          :model="editForm"
          :rules="editRules"
          label-width="100px"
        >
          <el-form-item label="邮箱地址" prop="email">
            <el-input v-model="editForm.email" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="editForm.password"
              type="password"
              show-password
              @input="checkPasswordStrength"
            >
              <template #append>
                <el-tooltip
                  content="密码应包含大小写字母、数字和特殊字符,长度至少8位"
                  placement="top"
                >
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </template>
            </el-input>
            <div class="password-strength" v-if="editForm.password">
              <span>密码强度:</span>
              <el-progress
                :percentage="passwordStrength"
                :color="passwordStrengthColor"
                :format="passwordStrengthText"
              />
            </div>
          </el-form-item>
          <!-- 显示邮箱类型但不能修改 -->
          <el-form-item label="邮箱类型">
            <el-tag :type="getMailTypeColor(editForm.mail_type)">
              {{ getMailTypeName(editForm.mail_type) }}
            </el-tag>
            <div class="form-tips">邮箱类型创建后不可修改</div>
          </el-form-item>
          <template v-if="editForm.mail_type === 'imap'">
            <div class="imap-tips">
              <h4>常用IMAP服务器配置:</h4>
              <p>Gmail: <code>imap.gmail.com</code> 端口: <code>993</code> SSL: 开启</p>
              <p>Outlook: <code>outlook.office365.com</code> 端口: <code>993</code> SSL: 开启</p>
              <p>QQ邮箱: <code>imap.qq.com</code> 端口: <code>993</code> SSL: 开启</p>
              <p>163邮箱: <code>imap.163.com</code> 端口: <code>993</code> SSL: 开启</p>
            </div>
            <el-form-item
              label="服务器"
              prop="server"
            >
              <el-input v-model="editForm.server">
                <template #append>
                  <el-tooltip content="IMAP服务器地址,如: imap.gmail.com" placement="top">
                    <el-icon><InfoFilled /></el-icon>
                  </el-tooltip>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item
              label="端口"
              prop="port"
            >
              <el-input-number
                v-model="editForm.port"
                :min="1"
                :max="65535"
                controls-position="right"
              />
              <div class="form-tips">常用端口: SSL-993, 非SSL-143</div>
            </el-form-item>
            <el-form-item label="使用SSL" prop="use_ssl">
              <el-switch v-model="editForm.use_ssl" />
            </el-form-item>
          </template>
          <template v-if="editForm.mail_type === 'outlook'">
            <el-form-item label="Client ID" prop="client_id">
              <el-input v-model="editForm.client_id" />
            </el-form-item>
            <el-form-item label="Refresh Token" prop="refresh_token">
              <el-input v-model="editForm.refresh_token" />
            </el-form-item>
          </template>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitEditForm">确定</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useEmailsStore } from '@/store/emails'
import api from '@/services/api'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import {
  Delete,
  Refresh,
  Plus,
  Download,
  Document,
  Message,
  View,
  Hide,
  InfoFilled
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import DOMPurify from 'dompurify'
import MailpeekEmailViewer from '@/components/MailpeekEmailViewer.vue'

const emailsStore = useEmailsStore()

// 状态
const loadingMails = ref(false)
const addEmailDialogVisible = ref(false)
const addEmailActiveTab = ref('single')
const mailContentDialogVisible = ref(false)
const mailListDialogVisible = ref(false)
const allMailListDialogVisible = ref(false)
const graphMailDialogVisible = ref(false)
const graphMailSearch = ref('')
const graphMailRecords = ref([])
const graphMailLastFetchedAt = ref('')
const graphMailLoadedFromDatabase = ref(false)
const graphEmail = ref(null)
const allMailSearch = ref('')
const allMailRecords = ref([])
const loadingAllMails = ref(false)
const loadingGraphMails = ref(false)
const addingEmail = ref(false)
const importing = ref(false)

// 添加邮箱表单引用
const addEmailFormRef = ref(null)
const batchImportFormRef = ref(null)

// 邮箱类型配置
const mailTypes = {
  outlook: {
    name: 'Outlook/Hotmail',
    color: 'primary'
  },
  imap: {
    name: 'IMAP邮箱',
    color: 'info'
  },
  gmail: {
    name: 'Gmail',
    color: 'danger'
  },
  qq: {
    name: 'QQ邮箱',
    color: 'success'
  }
}

// 获取邮箱类型名称
const getMailTypeName = (type) => {
  return mailTypes[type]?.name || type
}

// 获取邮箱类型颜色
const getMailTypeColor = (type) => {
  return mailTypes[type]?.color || 'default'
}

// 添加邮箱表单
const addEmailForm = ref({
  mail_type: 'outlook',
  email: '',
  password: '',
  client_id: '',
  refresh_token: '',
  server: '',
  port: 993,
  use_ssl: true
})

// 批量导入数据
const batchImport = reactive({
  data: '',
  mailType: 'outlook'
})

// 批量导入验证规则
const batchImportRules = {
  data: [
    { required: true, message: '导入数据不能为空', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback()
          return
        }

        const lines = value.trim().split('\n')
        let hasError = false

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim()
          if (!line) continue

          // 根据不同邮箱类型进行不同的验证
          if (batchImport.mailType === 'outlook') {
            const parts = line.split('----')
            if (parts.length !== 4) {
              hasError = true
              callback(new Error(`第 ${i + 1} 行格式错误，请使用"----"分隔邮箱、密码、客户端ID和RefreshToken`))
              break
            }

            if (!parts[0] || !parts[1] || !parts[2] || !parts[3]) {
              hasError = true
              callback(new Error(`第 ${i + 1} 行有空白字段，所有字段都必须填写`))
              break
            }

            // 简单的邮箱格式检查
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(parts[0])) {
              hasError = true
              callback(new Error(`第 ${i + 1} 行邮箱格式不正确`))
              break
            }
          }
        }

        if (!hasError) {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 添加邮箱表单验证规则
const addEmailRules = {
  mail_type: [{ required: true, message: '请选择邮箱类型', trigger: 'change' }],
  email: [{ required: true, message: '请输入邮箱地址', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  client_id: [{ required: true, message: '请输入Client ID', trigger: 'blur', validator: (rule, value, callback) => {
    if (addEmailForm.value.mail_type === 'outlook' && !value) {
      callback(new Error('请输入Client ID'))
    } else {
      callback()
    }
  }}],
  refresh_token: [{ required: true, message: '请输入Refresh Token', trigger: 'blur', validator: (rule, value, callback) => {
    if (addEmailForm.value.mail_type === 'outlook' && !value) {
      callback(new Error('请输入Refresh Token'))
    } else {
      callback()
    }
  }}],
  server: [{ required: true, message: '请输入服务器地址', trigger: 'blur', validator: (rule, value, callback) => {
    if (addEmailForm.value.mail_type === 'imap' && !value) {
      callback(new Error('请输入服务器地址'))
    } else {
      callback()
    }
  }}],
  port: [{ required: true, message: '请输入端口号', trigger: 'blur' }]
}

const selectedMail = ref(null)

// 计算属性
const emails = computed(() => emailsStore.emails)
const loading = computed(() => emailsStore.loading)
const currentEmail = computed(() => emailsStore.getEmailById(emailsStore.currentEmailId))
const mailRecords = computed(() => emailsStore.currentMailRecords)
const hasSelectedEmails = computed(() => emailsStore.hasSelectedEmails)
const selectedCount = computed(() => emailsStore.selectedEmailsCount)
const processingCount = computed(() =>
  Object.values(emailsStore.processingEmails || {}).filter((item) => item && item.progress >= 0 && item.progress < 100).length
)
const overviewStats = computed(() => [
  {
    label: '账户总数',
    value: emails.value.length,
    hint: '当前已接入的邮箱账号'
  },
  {
    label: '已选账号',
    value: selectedCount.value,
    hint: '用于批量操作的目标数量'
  },
  {
    label: '处理中',
    value: processingCount.value,
    hint: '正在收信或同步的任务'
  }
])
const filteredAllMailRecords = computed(() => {
  const query = allMailSearch.value.trim().toLowerCase()
  if (!query) {
    return allMailRecords.value
  }

  return allMailRecords.value.filter((mail) => {
    const searchTargets = [
      mail.email_address,
      mail.subject,
      mail.sender,
      typeof mail.content === 'object' ? mail.content?.content : mail.content
    ]

    return searchTargets.some((value) =>
      String(value || '').toLowerCase().includes(query)
    )
  })
})
const filteredGraphMailRecords = computed(() => {
  const query = graphMailSearch.value.trim().toLowerCase()
  if (!query) {
    return graphMailRecords.value
  }

  return graphMailRecords.value.filter((mail) => {
    const searchTargets = [
      mail.subject,
      mail.sender,
      typeof mail.content === 'object' ? mail.content?.content : mail.content,
      mail.body_preview
    ]

    return searchTargets.some((value) =>
      String(value || '').toLowerCase().includes(query)
    )
  })
})
const graphMailFetchButtonText = computed(() => {
  return '刷新 Graph 邮件'
})
const graphMailEmptyText = computed(() => {
  if (graphMailSearch.value.trim()) {
    return '没有匹配的 Graph 邮件'
  }

  if (graphMailLoadedFromDatabase.value) {
    return '数据库中暂无 Graph 邮件，请手动获取'
  }

  return '请点击刷新 Graph 邮件同步并保存到数据库'
})
const graphMailMemoryHint = computed(() => {
  if (!graphEmail.value) {
    return ''
  }

  if (graphMailLoadedFromDatabase.value) {
    return graphMailLastFetchedAt.value
      ? `当前显示数据库记录，最近同步时间：${formatDate(graphMailLastFetchedAt.value)}`
      : '当前显示数据库中的 Graph 邮件记录'
  }

  return '打开模态框后会读取数据库记录，刷新时同步 Graph 并保存'
})

// 方法
const refreshEmails = async () => {
  try {
    await emailsStore.fetchEmails()
    ElMessage.success('刷新成功')
  } catch (error) {
    console.error('获取邮箱列表失败:', error)
    ElMessage.error('获取邮箱列表失败，请检查网络连接')
  }
}

const normalizeMailRecord = (mail) => ({
  ...mail,
  subject: mail.subject || '(无主题)',
  sender: mail.sender || '(未知发件人)',
  received_time: mail.received_time || new Date().toISOString(),
  content: mail.content || '(无内容)',
  email_address: mail.email_address || currentEmail.value?.email || ''
})

const fetchAllMails = async () => {
  loadingAllMails.value = true
  try {
    const response = await api.getAllMailRecords({ limit: 1000 })
    const records = Array.isArray(response.data) ? response.data : []
    allMailRecords.value = records.map(normalizeMailRecord)
  } catch (error) {
    console.error('获取全部邮件记录失败:', error)
    ElMessage.error('获取全部邮件记录失败: ' + (error.message || '未知错误'))
  } finally {
    loadingAllMails.value = false
  }
}

const openAllMailsDialog = async () => {
  allMailListDialogVisible.value = true
  if (allMailRecords.value.length === 0) {
    await fetchAllMails()
  }
}

const canUseGraph = (email) => {
  return email?.mail_type === 'outlook' && !!email?.client_id && !!email?.refresh_token
}

const normalizeGraphMailRecord = (mail, emailAddress = '') => ({
  ...normalizeMailRecord(mail),
  email_address: mail.email_address || emailAddress,
  body_preview: mail.body_preview || '',
  is_read: Boolean(mail.is_read),
  has_attachments: Boolean(mail.has_attachments)
})

const isGraphMailRecord = (mail) => {
  return mail?.source === 'graph' || !!mail?.external_id || !!mail?.body_preview || !!mail?.parent_folder_id
}

const syncGraphMailRecordsFromStore = () => {
  if (!graphEmail.value || emailsStore.currentEmailId !== graphEmail.value.id) {
    return
  }

  const records = Array.isArray(emailsStore.currentMailRecords) ? emailsStore.currentMailRecords : []
  const graphRecords = records
    .filter(isGraphMailRecord)
    .map((mail) => normalizeGraphMailRecord(mail, graphEmail.value.email))

  graphMailRecords.value = graphRecords
  graphMailLoadedFromDatabase.value = true

  if (!graphMailLastFetchedAt.value && graphRecords.length > 0) {
    graphMailLastFetchedAt.value = graphRecords[0]?.created_at || ''
  }
}

const fetchGraphMails = async (row = graphEmail.value, options = {}) => {
  if (!canUseGraph(row)) {
    ElMessage.warning('当前邮箱缺少 Graph 所需凭据')
    return
  }

  const { sync = false, showSuccess = sync } = options

  loadingGraphMails.value = true
  graphEmail.value = row
  graphMailDialogVisible.value = true

  try {
    const response = await api.getGraphMessages(row.id, {
      folder: 'all',
      limit: 500,
      sync
    })

    const messages = Array.isArray(response.data?.messages) ? response.data.messages : []
    graphMailRecords.value = messages.map((mail) => normalizeGraphMailRecord(mail, row.email))
    graphMailLoadedFromDatabase.value = true

    if (sync) {
      graphMailLastFetchedAt.value = new Date().toISOString()
      if (showSuccess) {
        ElMessage.success(`已同步 ${response.data?.saved_count ?? 0} 封 Graph 邮件，当前数据库共有 ${graphMailRecords.value.length} 封`)
      }
    } else if (!graphMailLastFetchedAt.value && messages.length > 0) {
      graphMailLastFetchedAt.value = messages[0]?.created_at || ''
    }
  } catch (error) {
    console.error('获取 Graph 邮件失败:', error)
    ElMessage.error('获取 Graph 邮件失败: ' + (error.message || '未知错误'))
  } finally {
    loadingGraphMails.value = false
  }
}

const openGraphMailDialog = async (row) => {
  if (!canUseGraph(row)) {
    ElMessage.warning('当前邮箱缺少 Graph 所需凭据')
    return
  }

  graphEmail.value = row
  graphMailSearch.value = ''
  graphMailRecords.value = []
  graphMailLastFetchedAt.value = ''
  graphMailLoadedFromDatabase.value = false
  loadingGraphMails.value = false
  graphMailDialogVisible.value = true

  loadingGraphMails.value = true
  try {
    emailsStore.currentEmailId = row.id
    await emailsStore.fetchMailRecords(row.id)
    if (!emailsStore.isConnected) {
      syncGraphMailRecordsFromStore()
    }
  } catch (error) {
    console.error('获取 Graph 数据库邮件记录失败:', error)
    ElMessage.error('获取 Graph 数据库邮件记录失败: ' + (error.message || '未知错误'))
  } finally {
    loadingGraphMails.value = false
  }
}

watch(
  () => emailsStore.currentMailRecords,
  () => {
    if (graphMailDialogVisible.value) {
      syncGraphMailRecordsFromStore()
    }
  },
  { deep: true }
)

const handleSelectionChange = (selection) => {
  if (Array.isArray(selection)) {
    emailsStore.selectedEmails = selection.map(item => item.id)
  } else {
    emailsStore.selectedEmails = []
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除邮箱 ${row.email} 吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await emailsStore.deleteEmail(row.id)
      ElMessage.success('删除成功')
    } catch (error) {
      console.error('删除邮箱失败:', error)
      ElMessage.error('删除邮箱失败: ' + (error.message || '未知错误'))
    }
  }).catch(() => {
    // 取消删除，不做任何操作
  })
}

const handleBatchDelete = () => {
  if (!hasSelectedEmails.value) {
    ElMessage.warning('请先选择要删除的邮箱')
    return
  }

  const count = emailsStore.selectedEmailsCount
  // 确保是数组并且创建副本
  const emailIds = Array.isArray(emailsStore.selectedEmails) ?
    [...emailsStore.selectedEmails] : []

  if (emailIds.length === 0) {
    ElMessage.warning('没有选中有效的邮箱')
    return
  }

  ElMessageBox.confirm(
    `确定要删除选中的 ${count} 个邮箱吗？`,
    '批量删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await emailsStore.deleteEmails(emailIds)
      ElMessage.success(`已成功删除 ${count} 个邮箱`)
    } catch (error) {
      console.error('批量删除邮箱失败:', error)
      ElMessage.error('批量删除邮箱失败: ' + (error.message || '未知错误'))
    }
  }).catch(() => {
    // 取消删除，不做任何操作
  })
}

const handleCheck = async (row) => {
  try {
    const result = await emailsStore.checkEmail(row.id)

    // 检查结果，确定是否显示正在处理中的消息
    if (result && result.status === 'processing') {
      ElMessage.warning(result.message || '邮箱正在处理中，请稍候...')
    } else {
      ElMessage.info(`正在检查邮箱 ${row.email} 的邮件，请稍候...`)
    }
  } catch (error) {
    console.error('检查邮箱失败:', error)
    ElMessage.error('检查邮箱失败: ' + (error.message || '未知错误'))
  }
}

const handleBatchCheck = async () => {
  if (!hasSelectedEmails.value) {
    ElMessage.warning('请先选择要检查的邮箱')
    return
  }

  const count = emailsStore.selectedEmailsCount
  // 确保是数组并且创建副本
  const emailIds = Array.isArray(emailsStore.selectedEmails) ?
    [...emailsStore.selectedEmails] : []

  if (emailIds.length === 0) {
    ElMessage.warning('没有选中有效的邮箱')
    return
  }

  try {
    await emailsStore.checkEmails(emailIds)
    ElMessage.info(`正在检查 ${count} 个邮箱的邮件，请稍候...`)
  } catch (error) {
    console.error('批量检查邮箱失败:', error)
    ElMessage.error('批量检查邮箱失败: ' + (error.message || '未知错误'))
  }
}

const handleViewMails = async (row) => {
  loadingMails.value = true
  try {
    emailsStore.currentEmailId = row.id
    await emailsStore.fetchMailRecords(row.id)
    mailListDialogVisible.value = true
  } catch (error) {
    console.error('获取邮件记录失败:', error)
    ElMessage.error('获取邮件记录失败: ' + (error.message || '未知错误'))
  } finally {
    loadingMails.value = false
  }
}

const viewMailContent = (mail) => {
  // 增加防护检查，确保mail对象及其必要字段存在
  if (!mail) {
    ElMessage.warning('邮件数据不存在或格式错误');
    return;
  }

  // 创建一个格式化后的副本，防止直接修改原始数据
  const formattedMail = {
    ...normalizeMailRecord(mail)
  };

  selectedMail.value = formattedMail;
  mailContentDialogVisible.value = true;
}

const showAddEmailDialog = () => {
  resetAddEmailForm()
  addEmailDialogVisible.value = true
  addEmailActiveTab.value = 'single'
}

const handleAddOrImport = async () => {
  if (addEmailActiveTab.value === 'single') {
    await handleAddEmail()
  } else {
    await handleImport()
  }
}

const handleAddEmail = async () => {
  if (!addEmailFormRef.value) return

  try {
    // 表单验证
    await addEmailFormRef.value.validate()

    addingEmail.value = true
    const loading = ElLoading.service({
      lock: true,
      text: '正在添加邮箱...',
      background: 'rgba(0, 0, 0, 0.7)'
    })

    const formData = {
      email: addEmailForm.value.email,
      password: addEmailForm.value.password,
      mail_type: addEmailForm.value.mail_type
    }

    if (addEmailForm.value.mail_type === 'outlook') {
      formData.client_id = addEmailForm.value.client_id
      formData.refresh_token = addEmailForm.value.refresh_token
    } else if (addEmailForm.value.mail_type === 'imap') {
      formData.server = addEmailForm.value.server
      formData.port = addEmailForm.value.port
      formData.use_ssl = addEmailForm.value.use_ssl
    }

    await emailsStore.addEmail(formData)
    addEmailDialogVisible.value = false
    ElMessage.success('添加邮箱成功')

    // 刷新邮箱列表
    await refreshEmails()
  } catch (error) {
    console.error('添加邮箱失败:', error)
    ElMessage.error('添加邮箱失败: ' + (error.message || '未知错误'))
  } finally {
    addingEmail.value = false
    ElLoading.service().close()
  }
}

const handleImport = async () => {
  if (!batchImportFormRef.value) return

  try {
    await batchImportFormRef.value.validate()

    importing.value = true

    const importData = {
      data: batchImport.data.trim(),
      mail_type: batchImport.mailType
    }

    await emailsStore.importEmails(importData)
    ElMessage.info('正在处理导入请求，请稍候...')

    // 延迟刷新列表
    setTimeout(async () => {
      await refreshEmails()
      ElMessage.success('批量导入完成')
      addEmailDialogVisible.value = false
    }, 2000)
  } catch (error) {
    console.error('导入邮箱失败:', error)
    ElMessage.error('导入邮箱失败: ' + (error.message || '未知错误'))
  } finally {
    importing.value = false
  }
}

const resetAddEmailForm = () => {
  addEmailForm.value = {
    mail_type: 'outlook',
    email: '',
    password: '',
    client_id: '',
    refresh_token: '',
    server: '',
    port: 993,
    use_ssl: true
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '无';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss');
};

// 判断邮箱是否正在处理中
const isEmailProcessing = (email) => {
  const status = emailsStore.getProcessingStatus(email.id)
  return status && status.progress >= 0 && status.progress < 100
}

// 获取邮箱操作文本
const getEmailActionText = (email) => {
  return isEmailProcessing(email) ? '检查中...' : '检查邮件'
}

const togglePasswordVisibility = async (row) => {
  // 如果已经显示密码，则隐藏
  if (row.showPassword) {
    row.showPassword = false;
    return;
  }

  // 否则，从后端获取密码
  if (!row.password || row.password === '******') {
    row.passwordLoading = true;
    try {
      const response = await emailsStore.getEmailPassword(row.id);
      if (response && response.password) {
        row.password = response.password;
      }
    } catch (error) {
      console.error('获取密码失败:', error);
      ElMessage.error('获取密码失败: ' + (error.message || '未知错误'));
    } finally {
      row.passwordLoading = false;
    }
  }

  // 显示密码
  row.showPassword = true;
}

// 检查邮件内容是否为HTML格式
const isHtmlContent = (mail) => {
  if (!mail || !mail.content) return false;

  // 兼容新旧格式
  if (typeof mail.content === 'object') {
    return mail.content.has_html === true || mail.content.content_type === 'text/html';
  }

  // 旧格式，检查内容是否包含HTML标签
  const content = String(mail.content);
  return content.includes('<html') || content.includes('<body') ||
         content.includes('<div') || content.includes('<p>') ||
         content.includes('<table') || content.includes('<img');
}

// 获取邮件内容
const getMailContent = (mail) => {
  if (!mail) return '';

  // 兼容新旧格式
  if (typeof mail.content === 'object' && mail.content !== null) {
    return mail.content.content || '';
  }

  return mail.content || '';
}

// 截断内容
const truncateContent = (content) => {
  if (!content) return content;

  const maxLength = 1000; // 设置最大长度
  if (content.length > maxLength) {
    return content.slice(0, maxLength) + '...';
  }
  return content;
}

// 净化HTML内容，防止XSS攻击
const sanitizeHtml = (html) => {
  if (!html) return '';
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'a', 'b', 'br', 'div', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'i', 'img', 'li', 'ol', 'p', 'span', 'strong', 'table', 'tbody',
      'td', 'th', 'thead', 'tr', 'u', 'ul', 'font', 'blockquote', 'hr',
      'pre', 'code', 'col', 'colgroup', 'section', 'header', 'footer',
      'nav', 'article', 'aside', 'figure', 'figcaption', 'address', 'main',
      'caption', 'center', 'cite', 'dd', 'dl', 'dt', 'mark', 's', 'small',
      'strike', 'sub', 'sup'
    ],
    ALLOWED_ATTR: [
      'href', 'target', 'src', 'alt', 'style', 'class', 'id', 'width', 'height',
      'align', 'valign', 'bgcolor', 'border', 'cellpadding', 'cellspacing',
      'color', 'colspan', 'dir', 'face', 'frame', 'frameborder', 'headers',
      'hspace', 'lang', 'marginheight', 'marginwidth', 'nowrap', 'rel',
      'rev', 'rowspan', 'scrolling', 'shape', 'span', 'summary', 'title',
      'usemap', 'vspace', 'start', 'type', 'value', 'size', 'data-*'
    ]
  });
}

// 下载附件
const downloadAttachment = (attachmentId, filename) => {
  const token = localStorage.getItem('token')
  const downloadUrl = `/api/attachments/${attachmentId}/download`

  // 创建一个隐藏的a标签用于下载
  const link = document.createElement('a')
  link.href = downloadUrl
  link.setAttribute('download', filename)
  link.setAttribute('target', '_blank')

  // 添加认证头
  fetch(downloadUrl, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob)
    link.href = url
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  })
  .catch(error => {
    console.error('下载附件失败:', error)
    ElMessage.error('下载附件失败')
  })
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 添加编辑按钮的处理函数
const handleEdit = (email) => {
  // 确保use_ssl是布尔值
  const emailData = { ...email }
  if (emailData.mail_type === 'imap') {
    emailData.use_ssl = Boolean(emailData.use_ssl)
  }
  editForm.value = emailData
  editDialogVisible.value = true
}

// 引用和定义编辑对话框相关变量
const editDialogVisible = ref(false)
const editFormRef = ref(null)
const editForm = ref({
  id: null,
  email: '',
  password: '',
  mail_type: 'outlook',
  server: '',
  port: 993,
  use_ssl: true,
  client_id: '',
  refresh_token: ''
})

// 密码强度相关
const passwordStrength = ref(0)
const passwordStrengthColor = computed(() => {
  if (passwordStrength.value < 40) return '#F56C6C'
  if (passwordStrength.value < 80) return '#E6A23C'
  return '#67C23A'
})

const passwordStrengthText = (percentage) => {
  if (percentage < 40) return '弱'
  if (percentage < 80) return '中'
  return '强'
}

const checkPasswordStrength = (password) => {
  if (!password) {
    passwordStrength.value = 0
    return
  }

  let strength = 0
  // 检查长度
  if (password.length >= 8) strength += 20
  // 检查是否包含数字
  if (/\d/.test(password)) strength += 20
  // 检查是否包含小写字母
  if (/[a-z]/.test(password)) strength += 20
  // 检查是否包含大写字母
  if (/[A-Z]/.test(password)) strength += 20
  // 检查是否包含特殊字符
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 20

  passwordStrength.value = strength
}

// 编辑表单的规则
const editRules = {
  email: [
    { required: true, message: '邮箱地址不能为空', trigger: 'blur' },
    { type: 'email', message: '邮箱地址格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '密码不能为空', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6位', trigger: 'blur' }
  ],
  server: [
    { required: true, message: 'IMAP服务器地址不能为空', trigger: 'blur',
      // 仅当类型为imap时验证
      validator: (rule, value, callback) => {
        if (editForm.value.mail_type === 'imap' && !value) {
          callback(new Error('IMAP服务器地址不能为空'));
        } else {
          callback();
        }
      }
    }
  ],
  port: [
    {
      required: true,
      message: '端口号不能为空',
      trigger: 'blur',
      // 仅当类型为imap时验证
      validator: (rule, value, callback) => {
        if (editForm.value.mail_type === 'imap' && (!value || isNaN(value))) {
          callback(new Error('端口号必须是有效数字'));
        } else {
          callback();
        }
      }
    }
  ],
  client_id: [
    {
      required: true,
      message: 'Client ID不能为空',
      trigger: 'blur',
      // 仅当类型为outlook时验证
      validator: (rule, value, callback) => {
        if (editForm.value.mail_type === 'outlook' && !value) {
          callback(new Error('Client ID不能为空'));
        } else {
          callback();
        }
      }
    }
  ],
  refresh_token: [
    {
      required: true,
      message: 'Refresh Token不能为空',
      trigger: 'blur',
      // 仅当类型为outlook时验证
      validator: (rule, value, callback) => {
        if (editForm.value.mail_type === 'outlook' && !value) {
          callback(new Error('Refresh Token不能为空'));
        } else {
          callback();
        }
      }
    }
  ],
}

// 重置编辑表单
const resetEditForm = () => {
  editForm.value = {
    id: null,
    email: '',
    password: '******',  // 默认显示星号，实际修改时会获取真实密码
    mail_type: 'outlook',
    client_id: '',
    refresh_token: '',
    server: '',
    port: 993,
    use_ssl: true
  }
}

// 提交编辑表单
const submitEditForm = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()

    // 准备提交的数据
    const formData = { ...editForm.value }

    // 如果密码仍然是默认的星号，则不发送密码更新
    if (formData.password === '******') {
      delete formData.password
    }

    const loading = ElLoading.service({
      lock: true,
      text: '正在更新邮箱...',
      background: 'rgba(0, 0, 0, 0.7)'
    })

    await emailsStore.updateEmail(formData.id, formData)
    editDialogVisible.value = false

    // 刷新邮箱列表
    await refreshEmails()

    ElMessage.success('邮箱更新成功')
  } catch (error) {
    console.error('更新邮箱失败:', error)
    ElMessage.error('更新邮箱失败: ' + (error.message || '未知错误'))
  } finally {
    ElLoading.service().close()
  }
}

// 生命周期钩子
onMounted(() => {
  emailsStore.initWebSocketListeners()
  refreshEmails()
})
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-height: 100vh;
  padding: 0 0 1.25rem;
  overflow-x: hidden;
}

.emails-hero,
.emails-container {
  width: min(1280px, 100%);
  margin: 0 auto;
  padding: 0 1rem;
}

.emails-hero {
  display: grid;
  gap: 1rem;
}

.emails-hero-main {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  border-radius: 2rem;
  padding: 1.75rem;
}

.emails-hero-copy {
  max-width: 44rem;
}

.emails-hero-title {
  margin-top: 1rem;
  font-size: clamp(2rem, 3vw, 3rem);
  line-height: 1.05;
  font-weight: 900;
  letter-spacing: -0.03em;
  color: #0f172a;
}

.emails-hero-description {
  margin-top: 1rem;
  max-width: 40rem;
  font-size: 1rem;
  line-height: 1.85;
  color: #475569;
}

.emails-hero-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: flex-end;
  gap: 0.75rem;
}

.hero-action {
  min-height: 3rem;
  border: none;
  border-radius: 999px;
  padding: 0 1.2rem;
  font-weight: 700;
  box-shadow: none;
}

.hero-action-dark {
  background: linear-gradient(135deg, #0f172a, #155e75);
}

.hero-action-accent {
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
}

.hero-action-light {
  background: rgba(255, 255, 255, 0.8);
  color: #0f172a;
  border: 1px solid rgba(148, 163, 184, 0.22);
}

.emails-hero-stats {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.hero-stat-card {
  border-radius: 1.5rem;
  padding: 1.3rem 1.4rem;
}

.hero-stat-label {
  display: block;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #64748b;
}

.hero-stat-value {
  display: block;
  margin-top: 0.6rem;
  font-size: 2rem;
  font-weight: 900;
  color: #0f172a;
}

.hero-stat-hint {
  margin-top: 0.35rem;
  font-size: 0.92rem;
  line-height: 1.6;
  color: #64748b;
}

.emails-container {
  flex: 1;
}

.email-list-card {
  margin-bottom: 1rem;
  border-radius: 2rem;
  transition: transform var(--transition-normal), box-shadow var(--transition-normal);
}

.card-header {
  width: 100%;
}

.title-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.page-title {
  font-size: 1.6rem;
  color: #0f172a;
  margin: 0;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.card-subtitle {
  font-size: 0.96rem;
  line-height: 1.7;
  color: #64748b;
}

.toolbar {
  flex-wrap: wrap;
  padding: 0.85rem;
  border-radius: 1.35rem;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(241, 245, 249, 0.8));
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.email-table,
.mail-list-table {
  overflow: hidden;
  border-radius: 1.4rem;
}

.mail-type-tag {
  font-weight: 600;
}

.password-field {
  width: 100%;
}

.password-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.password-toggle-btn:hover {
  transform: scale(1.08);
}

.time-field {
  color: var(--secondary-text-color);
  font-size: 0.9rem;
}

.progress-container {
  width: 100%;
  padding: 0 5px;
}

.progress-message {
  font-size: 0.8rem;
  margin-top: 4px;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.action-btn {
  min-width: 76px;
  margin: 0;
  white-space: nowrap;
}

.mail-dialog-header {
  padding: 0 0 0.9rem 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.85);
}

.email-title {
  font-size: 1.15rem;
  margin: 0;
}

.all-mail-search {
  max-width: 420px;
}

.graph-mail-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.graph-mail-count {
  color: var(--secondary-text-color);
  font-size: 0.9rem;
}

.graph-mail-memory {
  color: var(--secondary-text-color);
  font-size: 0.85rem;
}

.subject-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.attachment-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.mail-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.mail-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  width: 100%;
}

.label {
  font-weight: 500;
  margin-right: 10px;
}

.mail-content {
  max-height: 400px;
  overflow-y: auto;
}

.mail-attachments {
  margin: 10px 0;
  padding: 12px;
  background: linear-gradient(180deg, #f0fdf4, #ecfdf5);
  border-radius: 1rem;
  border-left: 3px solid #22c55e;
}

.attachments-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.attachment-item {
  margin-bottom: 5px;
}

.mail-content-text {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.9rem;
  line-height: 1.7;
  padding: 14px;
  background-color: rgba(248, 250, 252, 0.9);
  border-radius: 1rem;
}

.html-content {
  max-width: 100%;
  overflow-x: auto;
  padding: 14px;
  background-color: rgba(248, 250, 252, 0.9);
  border-radius: 1rem;
  line-height: 1.6;
}

.html-content img {
  max-width: 100%;
  height: auto;
}

.html-content a {
  color: var(--primary-color);
  text-decoration: underline;
}

.html-content table {
  border-collapse: collapse;
  margin: 10px 0;
}

.html-content th,
.html-content td {
  border: 1px solid #ddd;
  padding: 8px;
}

.add-email-form {
  padding: 20px;
}

.w-full {
  width: 100%;
}

.import-help {
  margin-bottom: 20px;
  padding: 14px;
  background-color: rgba(248, 250, 252, 0.92);
  border-radius: 1rem;
  font-size: 0.9rem;
  line-height: 1.7;
}

.server-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
}

.server-field,
.port-field,
.config-info {
  color: var(--secondary-text-color);
}

.config-info {
  font-style: italic;
  font-size: 0.85rem;
}

.flex {
  display: flex;
  align-items: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.gap-sm {
  gap: 8px;
}

.gap-md {
  gap: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.text-center {
  text-align: center;
}

.text-primary {
  color: var(--primary-color);
}

.hover-scale {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hover-scale:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 18px 28px -22px rgba(15, 23, 42, 0.45);
}

:deep(.email-list-card.el-card),
:deep(.mail-list-dialog .el-dialog),
:deep(.mail-content-dialog .el-dialog),
:deep(.add-email-dialog .el-dialog) {
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9));
  box-shadow: 0 28px 80px -42px rgba(15, 23, 42, 0.38);
  backdrop-filter: blur(18px);
}

:deep(.email-list-card .el-card__header) {
  padding: 1.4rem 1.5rem 1rem;
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
}

:deep(.email-list-card .el-card__body) {
  padding: 0 1.5rem 1.5rem;
}

:deep(.el-table) {
  --el-table-header-bg-color: rgba(241, 245, 249, 0.86);
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.72);
  --el-table-row-hover-bg-color: rgba(236, 253, 245, 0.72);
  --el-table-border-color: rgba(226, 232, 240, 0.82);
  --el-table-text-color: #334155;
  --el-table-header-text-color: #0f172a;
}

:deep(.el-table th.el-table__cell) {
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

:deep(.el-table td.el-table__cell) {
  padding-top: 0.95rem;
  padding-bottom: 0.95rem;
}

:deep(.el-dialog) {
  border-radius: 1.6rem;
  overflow: hidden;
}

:deep(.el-dialog__header) {
  padding: 1.4rem 1.4rem 1rem;
  margin-right: 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.75);
}

:deep(.el-dialog__body) {
  padding: 1.25rem 1.4rem 1.4rem;
}

:deep(.el-dialog__footer) {
  padding: 0 1.4rem 1.4rem;
}

@media (max-width: 1024px) {
  .emails-hero-main {
    flex-direction: column;
  }

  .emails-hero-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .emails-hero,
  .emails-container {
    padding: 0 0.85rem;
  }

  .emails-hero-main,
  .email-list-card {
    border-radius: 1.5rem;
  }

  .emails-hero-stats {
    grid-template-columns: 1fr;
  }

  .card-header,
  .flex-between {
    flex-direction: column;
    align-items: flex-start;
  }

  .actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .action-buttons {
    justify-content: flex-start;
  }

  :deep(.email-list-card .el-card__header),
  :deep(.email-list-card .el-card__body) {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}
</style>
