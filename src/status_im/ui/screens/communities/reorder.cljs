(ns status-im.ui.screens.communities.reorder
  (:require          [status-im.ui.components.topbar :as topbar]
                     [status-im.utils.handlers :refer [<sub]]
                     [status-im.constants :as constants]
                     [status-im.ui.components.react :as react]
                     [status-im.ui.components.tabs :as tabs]
                     [status-im.i18n.i18n :as i18n]
                     [status-im.ui.screens.communities.reorder-chats :as reorder-chats]
                     [status-im.ui.screens.communities.reorder-categories :as reorder-categories]            [status-im.ui.screens.communities.community :as community]
                     [quo.design-system.colors :as colors]
                     [reagent.core :as reagent]))

(def state (reagent/atom {:tab :chats}))

(defn chats_and_categories []
  (let [{:keys [tab]} @state]
    [:<>
     [react/view {:flex-direction :row :margin 10 :border-radius 8 :background-color colors/blue-light}
      [tabs/tab-button state :chats (i18n/label :t/edit-chats) (= tab :chats)]
      [tabs/tab-button state :categories (i18n/label :t/edit-categories) (= tab :categories)]]
     (cond
       (= tab :chats)
       [reorder-chats/view]
       (= tab :categories)
       [reorder-categories/view])]))

(defn view []
  (let [{:keys [community-id]} (<sub [:get-screen-params])
        {:keys [id name images members permissions color]}
        (<sub [:communities/community community-id])]
    [:<> {:style {:flex 1}}
     [topbar/topbar
      {:content [community/toolbar-content id name color images
                 (not= (:access permissions) constants/community-no-membership-access)
                 (count members)]}]
     [chats_and_categories]]))
