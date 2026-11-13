# D-Bus 骨架：StatusNotifierItem + DBusMenu

本文是「../SKILL.md」的附录资料：托盘实现需要导出的最小 D-Bus 契约与可复制片段（Python + Gio）。
仅在实现或排查托盘的 D-Bus 层时按需加载。


    # 1) StatusNotifierItem 接口 XML（片段）——必须有 Activate 方法，双击才会打开
      <interface name="org.kde.StatusNotifierItem">
        <property name="Category" type="s" access="read"/>
        <property name="Id" type="s" access="read"/>
        <property name="Title" type="s" access="read"/>
        <property name="Status" type="s" access="read"/>
        <property name="WindowId" type="i" access="read"/>
        <property name="IconThemePath" type="s" access="read"/>
        <property name="Menu" type="o" access="read"/>
        <property name="ItemIsMenu" type="b" access="read"/>
        <property name="IconName" type="s" access="read"/>
        <property name="IconPixmap" type="a(iiay)" access="read"/>
        <method name="Activate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
        <method name="SecondaryActivate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
        <method name="ContextMenu"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
      </interface>

    # 2) DBusMenu 方法签名
      GetLayout(i parentId, i recursionDepth, as propertyNames) -> (u revision, (ia{sv}av) layout)
      GetGroupProperties(ai ids, as propertyNames) -> a(ia{sv})
      GetProperty(i id, s name) -> v
      Event(i id, s eventId, v data, u timestamp) -> ()
      AboutToShow(i id) -> b

    # 3) 构造 GetLayout 的 Python 片段（children 是 av，不是 a(ia{sv}av)！）
      def layout_node(item_id):
          children = [GLib.Variant.new_variant(layout_node(c)) for c in ITEM_CHILDREN[item_id]]
          av = GLib.Variant.new_array(GLib.VariantType.new("v"), children)
          return GLib.Variant.new_tuple(
              GLib.Variant("i", item_id),
              GLib.Variant("a{sv}", ITEM_PROPS[item_id]),
              av)
      invocation.return_value(GLib.Variant.new_tuple(GLib.Variant("u", 1), layout_node(0)))

    # 4) 导出对象并注册到 watcher
      bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
      bus.register_object("/StatusNotifierItem", sni_iface, sni_method_cb, sni_prop_cb, None)
      bus.register_object("/MenuBar", menu_iface, menu_method_cb, menu_prop_cb, None)
      bus.call_sync("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher",
                    "org.kde.StatusNotifierWatcher", "RegisterStatusNotifierItem",
                    GLib.Variant("(s)", (bus.get_unique_name(),)),
                    None, Gio.DBusCallFlags.NONE, 5000, None)

    # 5) 菜单 Event 分发
      id 10 -> xdg-open(state/url 或 http://127.0.0.1:PORT/)
      id 20 -> 杀 dsh web pid；等端口释放；setsid 调用 launcher；等端口 + url 更新
      id 30 -> 杀 dsh web pid；托盘退出
