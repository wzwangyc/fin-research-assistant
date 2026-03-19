#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能优化模块
功能：
1. 缓存机制
2. 懒加载
3. 内存管理
4. 性能监控
"""

import pickle
import hashlib
import time
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import json


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = 'cache', ttl: int = 3600):
        """
        初始化缓存
        
        Args:
            cache_dir: 缓存目录
            ttl: 默认 TTL（秒），默认 1 小时
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0
        }
    
    def _get_key(self, key: str) -> str:
        """生成缓存文件路径"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return str(self.cache_dir / f"{key_hash}.pkl")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        cache_file = self._get_key(key)
        
        if Path(cache_file).exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                
                # 检查 TTL
                if 'expires' in data and datetime.now() > data['expires']:
                    # 过期，删除
                    Path(cache_file).unlink()
                    self.stats['misses'] += 1
                    return default
                
                self.stats['hits'] += 1
                return data['value']
            except:
                self.stats['misses'] += 1
                return default
        
        self.stats['misses'] += 1
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        cache_file = self._get_key(key)
        expires = datetime.now() + timedelta(seconds=ttl or self.ttl)
        
        data = {
            'value': value,
            'expires': expires,
            'created': datetime.now()
        }
        
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        
        self.stats['writes'] += 1
    
    def delete(self, key: str):
        """删除缓存"""
        cache_file = self._get_key(key)
        if Path(cache_file).exists():
            Path(cache_file).unlink()
    
    def clear(self):
        """清空缓存"""
        for cache_file in self.cache_dir.glob('*.pkl'):
            cache_file.unlink()
    
    def cleanup_expired(self):
        """清理过期缓存"""
        count = 0
        for cache_file in self.cache_dir.glob('*.pkl'):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                
                if 'expires' in data and datetime.now() > data['expires']:
                    cache_file.unlink()
                    count += 1
            except:
                pass
        
        return count
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total if total > 0 else 0
        
        return {
            **self.stats,
            'total_requests': total,
            'hit_rate': f"{hit_rate:.1%}",
            'cache_size': len(list(self.cache_dir.glob('*.pkl')))
        }


def cached(ttl: Optional[int] = None, cache_manager: Optional[CacheManager] = None):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存 key
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            key = hashlib.md5(json.dumps(key_data, default=str).encode()).hexdigest()
            
            # 获取缓存
            manager = cache_manager or CacheManager()
            cached_result = manager.get(key)
            
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 保存缓存
            manager.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.timings = []
    
    def timer(self, name: str):
        """计时器装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                end = time.time()
                
                elapsed = end - start
                self.timings.append({
                    'name': name,
                    'func': func.__name__,
                    'elapsed': elapsed,
                    'timestamp': datetime.now()
                })
                
                print(f"⏱️ {name}: {elapsed:.3f}秒")
                return result
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        if not self.timings:
            return {'total_calls': 0}
        
        total_time = sum(t['elapsed'] for t in self.timings)
        avg_time = total_time / len(self.timings)
        
        # 按函数分组
        by_func = {}
        for timing in self.timings:
            func_name = timing['func']
            if func_name not in by_func:
                by_func[func_name] = {
                    'calls': 0,
                    'total_time': 0,
                    'avg_time': 0
                }
            by_func[func_name]['calls'] += 1
            by_func[func_name]['total_time'] += timing['elapsed']
        
        for func_name in by_func:
            by_func[func_name]['avg_time'] = by_func[func_name]['total_time'] / by_func[func_name]['calls']
        
        return {
            'total_calls': len(self.timings),
            'total_time': total_time,
            'avg_time': avg_time,
            'by_function': by_func
        }
    
    def report(self):
        """生成性能报告"""
        stats = self.get_stats()
        
        print("\n" + "="*70)
        print("性能报告")
        print("="*70)
        print(f"总调用次数：{stats['total_calls']}")
        print(f"总耗时：{stats['total_time']:.3f}秒")
        print(f"平均耗时：{stats['avg_time']:.3f}秒")
        
        print("\n按函数统计:")
        for func_name, func_stats in sorted(stats['by_function'].items(), 
                                           key=lambda x: x[1]['total_time'], 
                                           reverse=True):
            print(f"  {func_name}:")
            print(f"    调用次数：{func_stats['calls']}")
            print(f"    总耗时：{func_stats['total_time']:.3f}秒")
            print(f"    平均耗时：{func_stats['avg_time']:.3f}秒")


class LazyLoader:
    """懒加载器"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name):
        if self._module is None:
            import importlib
            self._module = importlib.import_module(self.module_name)
        return getattr(self._module, name)


# 全局缓存实例
default_cache = CacheManager(ttl=3600)  # 1 小时 TTL
perf_monitor = PerformanceMonitor()


if __name__ == '__main__':
    # 测试
    print("="*70)
    print("性能优化模块测试")
    print("="*70)
    
    # 测试缓存
    cache = CacheManager(cache_dir='test_cache', ttl=5)
    
    print("\n【缓存测试】")
    cache.set('test_key', {'data': 'test_value'})
    result = cache.get('test_key')
    print(f"获取缓存：{result}")
    
    # 测试装饰器
    @cached(ttl=10)
    def slow_function(x, y):
        time.sleep(0.5)
        return x + y
    
    print("\n【装饰器测试】")
    start = time.time()
    result1 = slow_function(1, 2)
    print(f"第一次调用：{result1} (耗时：{time.time() - start:.3f}秒)")
    
    start = time.time()
    result2 = slow_function(1, 2)
    print(f"第二次调用（缓存）：{result2} (耗时：{time.time() - start:.3f}秒)")
    
    # 测试性能监控
    print("\n【性能监控测试】")
    monitor = PerformanceMonitor()
    
    @monitor.timer("测试函数 1")
    def func1():
        time.sleep(0.1)
    
    @monitor.timer("测试函数 2")
    def func2():
        time.sleep(0.2)
    
    func1()
    func2()
    func1()
    
    monitor.report()
    
    # 测试懒加载
    print("\n【懒加载测试】")
    np = LazyLoader('numpy')
    print(f"numpy 版本：{np.__version__}")
