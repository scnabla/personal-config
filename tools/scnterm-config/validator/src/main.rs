// 独立配置编辑器的正则校验工具，不依赖 ScnTerm 源码或库。
use std::io::{self, Read};
fn check() -> Result<(), String> {
    let mut input = String::new();
    io::stdin().take(1024 * 1024 + 1).read_to_string(&mut input).map_err(|e| e.to_string())?;
    if input.len() > 1024 * 1024 { return Err("校验内容过大".into()); }
    let patterns: Vec<serde_json::Value> = serde_json::from_str(&input).map_err(|e| e.to_string())?;
    for (i, pattern) in patterns.iter().enumerate() {
        let raw=pattern.get("pattern").and_then(|v|v.as_str()).ok_or("缺少表达式")?;
        let escaped=regex::escape(raw);
        let text=if pattern.get("literal").and_then(|v|v.as_bool()).unwrap_or(false){&escaped}else{raw};
        regex::RegexBuilder::new(text)
            .case_insensitive(!pattern.get("case_sensitive").and_then(|v|v.as_bool()).unwrap_or(false))
            .size_limit(256 * 1024).dfa_size_limit(256 * 1024).build().map_err(|e| format!("第 {} 个正则表达式无效：{}", i + 1, e))?;
    }
    Ok(())
}
fn main() {
    let result = match check() { Ok(()) => serde_json::json!({"ok":true}), Err(e) => serde_json::json!({"ok":false,"error":e}) };
    println!("{}", result);
}
