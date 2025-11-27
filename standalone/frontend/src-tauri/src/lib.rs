use std::process::{Command, Child};
use std::path::PathBuf;

// standalone 폴더의 app/ 경로 찾기
fn get_standalone_root() -> PathBuf {
    std::env::current_exe()
        .expect("Failed to get exe path")
        .parent()
        .expect("Failed to get parent dir")
        .to_path_buf()
        .join("..")
        .join("..")
}

// FastAPI 서버 시작
fn start_backend() -> std::io::Result<Child> {
    let standalone_root = get_standalone_root();
    
    #[cfg(target_os = "windows")]
    let python_cmd = "python";
    
    #[cfg(not(target_os = "windows"))]
    let python_cmd = "python3";
    
    println!("Starting FastAPI backend from: {:?}", standalone_root);
    
    Command::new(python_cmd)
        .args(["-m", "uvicorn", "app.main:app", 
               "--host", "127.0.0.1", "--port", "8001",
               "--log-level", "error"])
        .current_dir(&standalone_root)
        .spawn()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 백엔드 서버 시작
    match start_backend() {
        Ok(_backend) => {
            println!("✅ FastAPI backend started");
            // 서버 준비 대기
            std::thread::sleep(std::time::Duration::from_secs(3));
        }
        Err(e) => {
            eprintln!("❌ Failed to start backend: {}", e);
            eprintln!("Make sure Python and dependencies are installed");
        }
    }
    
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
