import { useState, useRef, useCallback, useEffect } from 'react'

console.debug('[useDrag.ts] 加载模块')

interface DragPosition {
  x: number
  y: number
}

interface UseDragOptions {
  initialPosition?: DragPosition
  boundary?: {
    padding?: number
  }
}

export function useDrag(options: UseDragOptions = {}) {
  const {
    initialPosition = { x: 0, y: 0 },
    boundary = { padding: 20 }
  } = options

  const [position, setPosition] = useState<DragPosition>(initialPosition)
  const [isDragging, setIsDragging] = useState(false)

  const dragRef = useRef<HTMLDivElement>(null)
  const startPositionRef = useRef<DragPosition>({ x: 0, y: 0 })
  const dragStartPositionRef = useRef<DragPosition>({ x: 0, y: 0 })

  console.debug('[useDrag] 初始化 Hook', { initialPosition })

  // 确保位置在视口边界内
  const constrainToBoundary = useCallback((x: number, y: number): DragPosition => {
    if (!dragRef.current) {
      return { x, y }
    }

    const rect = dragRef.current.getBoundingClientRect()
    const padding = boundary.padding ?? 20

    const maxX = window.innerWidth - rect.width - padding
    const maxY = window.innerHeight - rect.height - padding

    return {
      x: Math.max(padding, Math.min(x, maxX)),
      y: Math.max(padding, Math.min(y, maxY))
    }
  }, [boundary.padding])

  const handleMouseDown = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    // 忽略不是鼠标左键或触摸的事件
    if ('touches' in e) {
      // 触摸事件
      if (e.touches.length !== 1) return
    } else {
      // 鼠标事件
      if (e.button !== 0) return
    }

    e.preventDefault()
    e.stopPropagation()

    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY

    startPositionRef.current = { x: clientX, y: clientY }
    dragStartPositionRef.current = { ...position }
    setIsDragging(true)

    console.debug('[useDrag] 开始拖拽', { startPosition: startPositionRef.current })
  }, [position])

  const handleMouseMove = useCallback((e: MouseEvent | TouchEvent) => {
    if (!isDragging) return

    e.preventDefault()

    const clientX = 'touches' in e ? e.touches[0].clientX : (e as MouseEvent).clientX
    const clientY = 'touches' in e ? e.touches[0].clientY : (e as MouseEvent).clientY

    const deltaX = clientX - startPositionRef.current.x
    const deltaY = clientY - startPositionRef.current.y

    const newX = dragStartPositionRef.current.x + deltaX
    const newY = dragStartPositionRef.current.y + deltaY

    const constrainedPosition = constrainToBoundary(newX, newY)
    setPosition(constrainedPosition)
  }, [isDragging, constrainToBoundary])

  const handleMouseUp = useCallback(() => {
    if (isDragging) {
      console.debug('[useDrag] 结束拖拽', { finalPosition: position })
      setIsDragging(false)
    }
  }, [isDragging, position])

  // 全局监听鼠标/触摸移动和释放事件
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove as any)
      window.addEventListener('mouseup', handleMouseUp)
      window.addEventListener('touchmove', handleMouseMove as any, { passive: false })
      window.addEventListener('touchend', handleMouseUp)

      return () => {
        window.removeEventListener('mousemove', handleMouseMove as any)
        window.removeEventListener('mouseup', handleMouseUp)
        window.removeEventListener('touchmove', handleMouseMove as any)
        window.removeEventListener('touchend', handleMouseUp)
      }
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  // 窗口大小变化时重新约束位置
  useEffect(() => {
    const handleResize = () => {
      setPosition(prev => constrainToBoundary(prev.x, prev.y))
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [constrainToBoundary])

  // 拖拽状态样式
  const dragStyle: React.CSSProperties = {
    transform: `translate(${position.x}px, ${position.y}px)`,
    cursor: isDragging ? 'grabbing' : 'auto',
    userSelect: isDragging ? 'none' : 'auto',
    touchAction: 'none'
  }

  // 拖拽手柄属性
  const dragHandleProps = {
    onMouseDown: handleMouseDown,
    onTouchStart: handleMouseDown,
    style: {
      cursor: 'move'
    } as React.CSSProperties
  }

  return {
    dragRef,
    position,
    setPosition,
    isDragging,
    dragStyle,
    dragHandleProps
  }
}
