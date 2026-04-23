<template>
  <div class="mailpeek-email-viewer">
    <div class="mail-header">
      <div class="header-row">
        <span class="label">发件人</span>
        <span class="value">{{ mail.sender || '-' }}</span>
      </div>
      <div class="header-row" v-if="mail.email_address">
        <span class="label">邮箱</span>
        <span class="value">{{ mail.email_address }}</span>
      </div>
      <div class="header-row" v-if="mail.received_time">
        <span class="label">时间</span>
        <span class="value">{{ formatDate(mail.received_time) }}</span>
      </div>
    </div>

    <div v-if="containsCidImages" class="inline-image-tip">
      检测到邮件包含 `cid:` 内联图片。如果这类图片仍未显示，通常需要后端额外提供 content-id 到附件的映射。
    </div>

    <EmailPreview
      v-if="previewHtml"
      class="mailpeek-preview"
      :html="previewHtml"
      client="raw"
      width="100%"
    />
    <el-empty v-else description="暂无邮件内容" />

    <EmailAttachments
      v-if="attachments.length > 0"
      :attachments="attachments"
      :loading="loadingAttachments"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import dayjs from 'dayjs'
import DOMPurify from 'dompurify'
import { EmailPreview } from '@mailpeek/preview'
import '@mailpeek/preview/style.css'
import EmailAttachments from '@/components/EmailAttachments.vue'

const props = defineProps({
  mail: {
    type: Object,
    required: true
  },
  attachments: {
    type: Array,
    default: () => []
  },
  loadingAttachments: {
    type: Boolean,
    default: false
  }
})

const MAIL_BASE_STYLE = `
  html, body {
    margin: 0;
    padding: 0;
    background: #ffffff;
    color: #1f2937;
    font-family: Arial, "Microsoft YaHei", sans-serif;
  }

  body {
    padding: 16px;
    line-height: 1.6;
    word-break: break-word;
  }

  img {
    max-width: 100%;
    height: auto;
  }

  table {
    max-width: 100%;
    border-collapse: collapse;
  }

  pre {
    white-space: pre-wrap;
    word-break: break-word;
  }
`

const formatDate = (value) => {
  if (!value) return '-'
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss')
}

const escapeHtml = (value) => String(value || '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

const rawMailContent = computed(() => {
  if (!props.mail) return ''

  if (typeof props.mail.content === 'object' && props.mail.content !== null) {
    return props.mail.content.content || props.mail.content.plain_text || ''
  }

  return props.mail.content || ''
})

const isHtmlContent = computed(() => {
  if (!props.mail || !props.mail.content) return false

  if (typeof props.mail.content === 'object' && props.mail.content !== null) {
    return props.mail.content.has_html === true ||
      props.mail.content.content_type === 'text/html' ||
      props.mail.content.content_type?.includes('html')
  }

  const content = String(rawMailContent.value || '').toLowerCase()
  return content.includes('<html') ||
    content.includes('<body') ||
    content.includes('<div') ||
    content.includes('<table') ||
    content.includes('<img') ||
    content.includes('<style')
})

const sanitizeHtmlDocument = (html) => {
  if (!html) return ''

  return DOMPurify.sanitize(html, {
    WHOLE_DOCUMENT: true,
    ADD_TAGS: ['html', 'head', 'body', 'meta', 'style', 'link', 'title'],
    ADD_ATTR: [
      'style', 'class', 'id', 'src', 'srcset', 'alt', 'href', 'target', 'rel',
      'width', 'height', 'align', 'valign', 'bgcolor', 'border', 'cellpadding',
      'cellspacing', 'colspan', 'rowspan', 'role', 'aria-label', 'aria-hidden',
      'dir', 'lang', 'xmlns', 'viewBox', 'data-*'
    ],
    FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button']
  })
}

const buildHtmlDocument = (content, htmlMode) => {
  if (!content) return ''

  if (htmlMode) {
    const safeHtml = sanitizeHtmlDocument(content)

    if (/<html[\s>]/i.test(safeHtml)) {
      if (/<head[\s>]/i.test(safeHtml)) {
        return safeHtml.replace(
          /<\/head>/i,
          `<base target="_blank" /><style>${MAIL_BASE_STYLE}</style></head>`
        )
      }

      return safeHtml.replace(
        /<html([^>]*)>/i,
        '<html$1><head><base target="_blank" /><style>' + MAIL_BASE_STYLE + '</style></head>'
      )
    }

    return `
      <html>
        <head>
          <base target="_blank" />
          <style>${MAIL_BASE_STYLE}</style>
        </head>
        <body>${safeHtml}</body>
      </html>
    `
  }

  return `
    <html>
      <head>
        <base target="_blank" />
        <style>${MAIL_BASE_STYLE}</style>
      </head>
      <body>
        <pre>${escapeHtml(content)}</pre>
      </body>
    </html>
  `
}

const previewHtml = computed(() => buildHtmlDocument(rawMailContent.value, isHtmlContent.value))

const containsCidImages = computed(() => /cid:/i.test(String(rawMailContent.value || '')))
</script>

<style scoped>
.mailpeek-email-viewer {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mail-header {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  padding: 12px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.header-row {
  display: flex;
  gap: 8px;
  min-width: 220px;
}

.label {
  color: #64748b;
  font-weight: 600;
}

.value {
  color: #0f172a;
  word-break: break-word;
}

.inline-image-tip {
  padding: 10px 12px;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.mailpeek-preview {
  width: 100%;
}

.mailpeek-preview :deep(.mp-shell),
.mailpeek-preview :deep(.mp-preview-shell),
.mailpeek-preview :deep(.mp-preview-frame) {
  width: 100%;
  max-width: 100%;
}

@media (max-width: 768px) {
  .mail-header {
    padding: 12px;
  }

  .header-row {
    min-width: 100%;
  }
}
</style>
