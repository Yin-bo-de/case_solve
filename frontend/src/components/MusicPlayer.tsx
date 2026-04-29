import { useEffect, useRef } from 'react'
import { useUIStore } from '@/store'
import musicFile from '../../assert/案件推理背景音乐_watermark.mp3'

console.debug('[MusicPlayer] 加载模块')

function MusicOnIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    </svg>
  )
}

function MusicOffIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="1" y1="1" x2="23" y2="23" />
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    </svg>
  )
}

export default function MusicPlayer() {
  const { musicStarted, musicPlaying, setMusicPlaying } = useUIStore()
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // 第一次 musicStarted 变为 true 时初始化 Audio 对象
  useEffect(() => {
    if (!musicStarted) return
    if (audioRef.current) return  // 已初始化，避免重复创建

    console.info('[MusicPlayer] 初始化 Audio 对象')
    const audio = new Audio(musicFile)
    audio.loop = true
    audio.volume = 0.5
    audioRef.current = audio

    audio.play()
      .then(() => {
        setMusicPlaying(true)
        console.info('[MusicPlayer] 自动播放成功')
      })
      .catch(() => {
        setMusicPlaying(false)
        console.warn('[MusicPlayer] 浏览器阻止自动播放，等待用户点击')
      })
  }, [musicStarted, setMusicPlaying])

  // 响应 musicPlaying 状态变化（用户点击切换）
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    if (musicPlaying) {
      audio.play().catch(() => {
        setMusicPlaying(false)
        console.warn('[MusicPlayer] 播放失败')
      })
    } else {
      audio.pause()
    }
  }, [musicPlaying, setMusicPlaying])

  // 不在游戏阶段时不渲染按钮
  if (!musicStarted) return null

  const toggle = () => {
    console.info('[MusicPlayer] 用户切换音乐', { current: musicPlaying })
    setMusicPlaying(!musicPlaying)
  }

  return (
    <button
      className={`music-player-btn${musicPlaying ? ' music-player-btn--playing' : ''}`}
      onClick={toggle}
      title={musicPlaying ? '关闭背景音乐' : '开启背景音乐'}
      type="button"
    >
      {musicPlaying ? <MusicOnIcon /> : <MusicOffIcon />}
    </button>
  )
}
