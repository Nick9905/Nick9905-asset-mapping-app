import re
import os

def clean_file():
    try:
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        original_file = os.path.join(current_dir, 'asset system.py')
        cleaned_file = os.path.join(current_dir, 'asset system_cleaned.py')
        
        print("正在读取 asset system.py 文件...")
        
        # 检查文件是否存在
        if not os.path.exists(original_file):
            print(f"❌ 错误: 找不到文件 {original_file}")
            return False
            
        with open(original_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"原文件大小: {len(content)} 字符")
        
        # 清理非打印字符
        cleaned_content = re.sub(r'[\u00A0\u2000-\u200B\u2028\u2029]', ' ', content)
        
        # 统计清理的字符数
        original_length = len(content)
        cleaned_length = len(cleaned_content)
        
        # 保存清理后的文件
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print("✅ 文件清理完成！")
        print(f"清理后文件大小: {cleaned_length} 字符")
        print(f"已保存为: asset system_cleaned.py")
        
        if original_length != cleaned_length:
            print(f"⚠️  发现并清理了 {original_length - cleaned_length} 个不可见字符")
            return True
        else:
            print("✅ 没有发现不可见字符")
            return False
            
    except Exception as e:
        print(f"❌ 清理过程中出现错误: {str(e)}")
        return False

if __name__ == "__main__":
    clean_file()
