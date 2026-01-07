# Sora2故事板视频

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v2/videos/generations:
    post:
      summary: Sora2故事板视频
      deprecated: false
      description: >-
        提示词按照以下格式传即可自动启用故事板

        Shot 1:\nduration: 7.5sec\nScene: 飞机起飞\n\nShot 2:\nduration:
        7.5sec\nScene: 飞机降落
      tags:
        - 视频模型/统一格式接口/Sora2 视频
      parameters:
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
        - name: Authorization
          in: header
          description: ''
          required: false
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
            default: Bearer {{YOUR_API_KEY}}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                prompt:
                  type: string
                  x-apifox-mock: >-
                    Shot 1:\nduration: 7.5sec\nScene: 飞机起飞\n\nShot 2:\nduration:
                    7.5sec\nScene: 飞机降落
                model:
                  type: string
                  x-apifox-mock: sora-2
                  enum:
                    - sora-2
                    - sora-2-pro
                  x-apifox-enum:
                    - value: sora-2
                      name: ''
                      description: ''
                    - value: sora-2-pro
                      name: ''
                      description: 支持hd、15s
                aspect_ratio:
                  type: string
                  enum:
                    - '16:9'
                    - '9:16'
                  x-apifox-enum:
                    - value: '16:9'
                      name: 横屏
                      description: ''
                    - value: '9:16'
                      name: 竖屏
                      description: ''
                  x-apifox-mock: '16:9'
                  description: 输出比例
                hd:
                  type: boolean
                  x-apifox-mock: 'true'
                  description: 是否生成高清，默认false；高清会导致生成速度更慢; 仅 sora-2-pro 支持
                duration:
                  type: string
                  description: 视频时长；仅 sora-2-pro 支持25s
                  x-apifox-mock: '10'
                  enum:
                    - '10'
                    - '15'
                    - '25'
                  x-apifox-enum:
                    - value: '10'
                      name: ''
                      description: ''
                    - value: '15'
                      name: ''
                      description: ''
                    - value: '25'
                      name: ''
                      description: 仅 sora-2-pro 支持25s；当25时，HD不起作用
                notify_hook:
                  type: string
                  description: https://xxxx.com/callback
                watermark:
                  type: boolean
                  description: 默认 false
                  x-apifox-mock: 'false'
                private:
                  type: boolean
                  description: |
                    是否隐藏视频，true-视频不会发布，同时视频无法进行 remix(二次编辑)， 默认为 false
              required:
                - prompt
                - model
              x-apifox-orders:
                - prompt
                - model
                - aspect_ratio
                - hd
                - duration
                - notify_hook
                - watermark
                - private
            example:
              prompt: |-
                Shot 1:
                duration: 7.5sec
                Scene: 飞机起飞

                Shot 2:
                duration: 7.5sec
                Scene: 飞机降落
              model: sora-2
              aspect_ratio: '16:9'
              hd: false
              duration: '10'
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
                x-apifox-orders: []
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频模型/统一格式接口/Sora2 视频
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-385318417-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```