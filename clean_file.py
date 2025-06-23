import re

def clean_file():
    try:
        # 读取原文件
        print("正在读取 asset system.py 文件...")
        with open('asset system.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"原文件大小: {len(content)} 字符")
        
        # 清理非打印字符
        # 替换不间断空格和其他不可见字符为普通空格
        cleaned_content = re.sub(r'[\u00A0\u2000-\u200B\u2028\u2029]', ' ', content)
        
        # 统计清理的字符数
        original_length = len(content)
        cleaned_length = len(cleaned_content)
        
        # 保存清理后的文件
        with open('asset system_cleaned.py', 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print("✅ 文件清理完成！")
        print(f"清理后文件大小: {cleaned_length} 字符")
        print(f"已保存为: asset system_cleaned.py")
        
        if original_length != cleaned_length:
            print(f"⚠️  发现并清理了 {original_length - cleaned_length} 个不可见字符")
        else:
            print("✅ 没有发现不可见字符")
            
    except FileNotFoundError:
        print("❌ 错误: 找不到 'asset system.py' 文件")
        print("请确保此脚本与你的主文件在同一个文件夹中")
    except Exception as e:
        print(f"❌ 清理过程中出现错误: {str(e)}")

if __name__ == "__main__":
    clean_file()
