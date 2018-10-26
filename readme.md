# cmder shell builder
这是一个生成批处理脚本的小工具。

## 作用
这是一个为[Cmder](http://cmder.net/)准备的小工具。Cmder是一个Windows平台下的终端软件，可以根据自订命令构建想要的terminal。  
不过Cmder的UI和部分操作逻辑比较古老，不够清爽，比如新建一个新的标签页，要么使用`CTRL + T`打开新建页，要么使用`CTRL + ALT + <num>`来调用目标序列号的Task，一个不够简洁，一个不够直观。  
这个小工具能够生成一个脚本，使Cmder打开标签页后使用命令行的方式手动选取想使用的终端。这个脚本十分简易，当然可以手写，但是如果要修改脚本总归是很麻烦的。  

## 部署
基于`python3.6.1`。不依赖第三方包。  
将源代码放置在任意位置，复制一份`config.json.example`生成`config.json`，并参考下面的规范，根据需要修改。  
之后运行源代码即可生成脚本。
```
python cmder_shell.py
```
在Cmder内，添加新的Task，命令执行`call <bat path>`即可使用脚本来打开新终端。建议配合热键使用。

## 配置文件编写规范
总的来说，`config.json`的内容是这样的：
```json
{
    "common": {
        "compile": ["<compile goal format>"]
    },
    "configs": [
        { 
            "filename": "<filename and path>",
            "title": "<title of terminal while selecting>",
            "use_index": true,
            "lines": {
                "head": "<format of head text>",
                "item": "<format of each item text>",
                "select": "<format of select notice text>"
            },
            "choices": [
                {
                    "toggle": ["<what inputs raw can toggle this choice>"],
                    "terminal_title": "<title of terminal in this choice>",
                    "command": "<command of this choice>"
                }
            ],
            "else_choice": {
                "terminal_title": "<title of terminal in this choice>",
                "command": "<command of this choice>"
            }
        }
    ]
}
```

### common
(_可省略_)common这个结构可以整个省略。会启用默认参数。  
这一部分配置了一些公共选项，目前只有`compile`这一个参数。  
* `compile`: 编译到哪种类型的脚本语言。目前只支持`bat`批处理脚本，因为这是Windows下可以最快执行的脚本就只做了这一种。

### configs
这一部分定义多个要编译的批处理文件。每一个`{}`都是一个被定义的文件。下面针对单个FileConfig描述参数。  
* `filename`: 文件要存储的文件名位置。这个不包括扩展名，扩展名会被自动补充。
* `title`: 当使用这个脚本，进入选择状态时，终端显示的标题。
* `use_index`: (_可省略_, 默认`true`)一个统一的开关，是否在选择时允许通过输入choice的序号进行选择。
* `lines`: (_可省略_, 启用默认参数)这一部分自定义选择时的简洁语言内容。  
    所有语言内容的编写都可以使用变量替换，具体规则见稍后。  
    * `head`: (_可省略_, 默认`[SELECT $+title]`)进入select会首先打印一行标题。定义这个标题的格式。  
        可用的keymap为file config范围的keymap。
    * `item`: (_可省略_, 默认` $index $title`)select会打印所有可选项。使用这个定义可选项格式。  
        可用的keymap为choice范围的keymap。
    * `select`: (_可省略_, 默认`SELECT:`)在输入选择之前显示的句子。
        可用的keymap为file config范围的keymap。
* `choices`: 列出所有可选项。每一个`{}`都是一个被定义的可选项。下面针对单个choice进行描述。
    * `toggle`: 一个列表，定义了哪些输入能触发本选项。
    * `terminal_title`: 进入本选项的命令之后，终端显示的标题。  
        可以使用变量替换，可用的keymap为choice范围的keymap。
    * `command`: 本选项将执行的命令。  
        可以使用变量替换，可用的keymap为choice范围的keymap。
* `else_choice`: (_可省略_, 默认`null`)如果不匹配上面的任何一类输入，那么触发else选项。  
    else选项的编写规则与其他choice基本类似，但是不需要编写`toggle`。

### 变量替换
一部分text是支持变量替换的格式化字符串，可以编写这些字符串替换一些内容。

#### 如何替换
在字符串里编写`$var_name`即可。`var_name`包含字母、数字、`_`符号。目前版本不支持`$`字符转义。  
有一些额外的用法。在`$`和`var_name`之间添加`+`符号，可使结果转换为全大写；添加`-`符号，可使结果转换为全小写。

#### 替换源在哪里
上面提到的keymap即为替换变量的来源。  
keymap有两个范围。
* file config范围：变量从`configs`定义的`{}`配置里获取。除了`lines`, `use_index`, `choices`, `else_choice`之外的任何键值都会被纳入keymap。这意味着你可以在这个配置范围里自由添加任何字段。
* choice范围：变量从`choices`定义的`{}`配置里获取。除了`toggle`, `terminal_title`, `command`之外的任何键值都会被纳入keymap。这意味着你可以在这个配置范围里自由添加任何字段。  
    此外choice范围还有一些特殊规则。
    * `index`变量将总是被纳入keymap，它的值相当于choice的序号。
    * `title`不是一个被显式定义的字段，你可以随意定义它，不过如果你没有定义它，则它的默认值会变成`toggle`的第一项，除非`toggle`没有可用值。

#### command命令里的别的东西
在command命令内，`%%arg%%`将会被识别为你输入的内容。这个常用于`else_choice`选项。

## 示例配置文件
下面是一份示例配置。它包含了两个脚本文件，一个用于打开本地终端，一个用于SSH连接远程终端。
```json
{
    "configs": [
        {
            "filename": "C:\\Application\\Cmder\\terminal",
            "title": "Local Terminal",
            "choices": [
                {
                    "toggle": ["cmder", "c"],
                    "terminal_title": "Cmder",
                    "command": "cmd /k \"\"C:\\Application\\Cmder\\vendor\\init.bat\"\""
                },
                {
                    "toggle": ["cmd"],
                    "terminal_title": "Cmd",
                    "command": "cmd"
                },
                {
                    "toggle": ["powershell", "ps"],
                    "terminal_title": "PowerShell",
                    "command": "powershell"
                },
                {
                    "toggle": ["python", "py"],
                    "terminal_title": "Python3.6",
                    "command": "python"
                }
            ]
        },
        {
            "filename": "C:\\Application\\Cmder\\ssh",
            "title": "SSH Terminal",
            "lines": {
                "item": " $index $title[$ip]"
            },
            "choices": [
                {
                    "user": "heer", "ip": "worker",
                    "toggle": ["worker"],
                    "terminal_title": "[SSH]worker",
                    "command": "ssh $user@$ip"
                },
                {
                    "user": "heer", "ip": "myserver",
                    "toggle": ["myserver", "my", "heerkirov"],
                    "title": "myserver/heerkirov",
                    "terminal_title": "[SSH]myserver",
                    "command": "ssh $user@$ip"
                }
            ],
            "else_choice": {
                "terminal_title": "[SSH]Terminal",
                "command": "ssh %%arg%%"
            }
        }
    ]
}
```