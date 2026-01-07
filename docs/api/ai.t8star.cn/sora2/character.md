# 创建角色 Character

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /sora/v1/characters:
    post:
      summary: 创建角色 Character
      deprecated: false
      description: |
        创建角色，后续可用于 @ 调用，注意调用角色需要跟 prompt 有空格隔开
        例如：@{角色1Username} 在一个舞台上和 @{角色2Username} 牵手跳舞

        参数 url、 from_task 二选一，必须设置一个

        接口说明
        角色客串功能:
        你可以把生成的或者上传你自己的视频，把任何角色对象提取出来，加入视频中作为“客串角色”
        用户不仅能客串自己，还可以创建生活中的角色(如宠物、朋友)或纯想象的角色(如怪物、英雄、奇幻生物)
        只需上传相机里的视频(如宠物鸭子视频)，或直接生成全新角色，甚至从日常物品(如饼干罐)衍生出有趣面孔。
        任何东西都能变身客串，激发无限脑洞

        PS: 这个角色指的是物品，不是人物，人物要走 face id 录入暂不支持上传
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
                url:
                  type: string
                  description: |
                    视频中包含需要创建的角色，视频必须有声音、有角色;参数 url、 from_task 二选一，必须设置一个
                  x-apifox-mock: https://xxxx
                timestamps:
                  type: string
                  description: |
                    单位秒，例如 ‘1,2’ 是指视频的1～2秒中出现的角色，注意范围差值最大 3 秒最小 1 秒
                  x-apifox-mock: 1,2
                from_task:
                  type: string
                  description: 可以根据已经生成的任务 id，来创建角色;参数 url、 from_task 二选一，必须设置一个
              required:
                - timestamps
              x-apifox-orders:
                - timestamps
                - url
                - from_task
            example:
              url: >-
                https://filesystem.site/cdn/20251030/javYrU4etHVFDqg8by7mViTWHlMOZy.mp4
              timestamps: 1,3
              from_task: video_637efe22-3b6a-47ad-ab02-ee01a686a0bd
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                    description: 角色id
                  username:
                    type: string
                    description: 角色名称，用于放在提示词中 @{username}
                  permalink:
                    type: string
                    description: 角色主页，跳转到 openai 角色主页
                  profile_picture_url:
                    type: string
                    description: 角色头像
                required:
                  - id
                  - username
                  - permalink
                  - profile_picture_url
                x-apifox-orders:
                  - id
                  - username
                  - permalink
                  - profile_picture_url
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频模型/统一格式接口/Sora2 视频
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-374618722-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```