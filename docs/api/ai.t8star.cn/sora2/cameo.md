# Sora2 使用角色客串

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
      summary: Sora2 使用角色客串
      deprecated: false
      description: |-
        角色客串功能:
        你可以把生成的或者上传你自己的视频，把任何角色对象提取出来，加入视频中作为“客串角色”
        用户不仅能客串自己，还可以创建生活中的角色(如宠物、朋友)或纯想象的角色(如怪物、英雄、奇幻生物)
        只需上传相机里的视频(如宠物鸭子视频)，或直接生成全新角色，甚至从日常物品(如饼干罐)衍生出有趣面孔。
        任何东西都能变身客串，激发无限脑洞

        PS: 这个角色指的是物品，不是人物，人物要走 face id 录入暂不支持上传
        注意调用角色需要跟 prompt 有空格隔开
        例如：@{角色1Username} 在一个舞台上和 @{角色2Username} 牵手跳舞
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
                  x-apifox-mock: '@{角色1Username} 在一个舞台上和 @{角色2Username} 牵手跳舞'
                  description: |-
                    注意调用角色需要跟 prompt 有空格隔开
                    例如：@{角色1Username} 在一个舞台上和 @{角色2Username} 牵手跳舞
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
                  x-apifox-mock: 'false'
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
                      description: 仅 sora-2-pro 支持25s
                images:
                  type: array
                  items:
                    type: string
                  description: 图片列表，支持url、base64
                notify_hook:
                  type: string
                watermark:
                  type: boolean
                  x-apifox-mock: 'false'
                private:
                  type: boolean
                  description: |
                    是否隐藏视频，true-视频不会发布，同时视频无法进行 remix(二次编辑)， 默认为 false
                  x-apifox-mock: 'false'
                character_url:
                  type: string
                  description: |
                    创建角色需要的视频链接，注意视频中一定不能出现真人，否则会失败
                  x-apifox-mock: >-
                    https://filesystem.site/cdn/20251030/javYrU4etHVFDqg8by7mViTWHlMOZy.mp4
                character_timestamps:
                  type: string
                  description: |
                    视频角色出现的秒数范围，格式 `{start},{end}`, 注意 end-start 的范围 1～3秒
                  x-apifox-mock: 1,3
              required:
                - prompt
                - model
              x-apifox-orders:
                - prompt
                - model
                - images
                - aspect_ratio
                - hd
                - duration
                - notify_hook
                - watermark
                - private
                - character_url
                - character_timestamps
            examples: {}
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
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-369451139-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```