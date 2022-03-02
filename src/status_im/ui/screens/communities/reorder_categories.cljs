(ns status-im.ui.screens.communities.reorder-categories
  (:require [quo.core :as quo]
            [quo.react-native :as rn]
            [reagent.core :as reagent]
            [status-im.i18n.i18n :as i18n]
            [status-im.utils.utils :as utils]
            [status-im.constants :as constants]
            [quo.design-system.colors :as colors]
            [status-im.utils.platform :as platform]
            [status-im.communities.core :as communities]
            [status-im.utils.handlers :refer [>evt <sub]]
            [status-im.ui.components.icons.icons :as icons]
            [status-im.ui.screens.communities.styles :as styles]
            [status-im.ui.screens.communities.community :as community]))

(def data (reagent/atom []))

(defn show-delete-category-confirmation [community-id category-id]
  (utils/show-confirmation
   {:title               (i18n/label :t/delete-confirmation)
    :content             (i18n/label :t/delete-category-confirmation)
    :confirm-button-text (i18n/label :t/delete)
    :on-accept           #(>evt [:delete-community-category community-id category-id])}))

(defn category-item
  [{:keys [id name community-id]} is-active? drag]
  (let [background-color (if is-active? colors/gray-lighter colors/white)]
    [:<> {:style {:flex 1}}
     [rn/view {:accessibility-label :category-item
               :style               (merge styles/category-item
                                           {:background-color background-color})}
      [rn/touchable-opacity
       {:accessibility-label :delete-category-button
        :on-press            #(show-delete-category-confirmation community-id id)}
       [icons/icon :main-icons/delete-circle {:no-color true}]]
      [rn/view {:flex 1}
       [rn/text {:style {:font-size 17 :margin-left 10 :color colors/black}} name]]
      [rn/touchable-opacity {:accessibility-label :category-drag-handle
                             :on-long-press       drag
                             :delay-long-press    100
                             :style               {:padding 20}}
       [icons/icon :main-icons/reorder-handle {:no-color true :width 18 :height 12}]]]]))

(defn render-fn
  [{:keys [chat-type] :as item} _ _ _ is-active? drag]
  (when-not (= chat-type constants/community-chat-type)
    [category-item item is-active? drag]))

(defn update-local-atom [data-js]
  (reset! data data-js)
  (reagent/flush))

(defn on-drag-end-category [from to data-js]
  (let [{:keys [id community-id position]} (get @data from)]
    (when (and (< to (count @data)) (not= position to) (not= id ""))
      (update-local-atom data-js)
      (>evt [::communities/reorder-community-category community-id id to]))))

(defn reset-data [categories]
  (reset! data categories))

(defn draggable-list []
  [rn/draggable-flat-list
   {:key-fn               :id
    :data                 @data
    :render-fn            render-fn
    :autoscroll-threshold (if platform/android? 150 250)
    :autoscroll-speed     (if platform/android? 10 150) ;; TODO - Use same speed for both ios and android
    :container-style      {:margin-bottom 108}          ;;        after bumping react native version to > 0.64 
    :on-drag-end-fn       on-drag-end-category}])

(defn view []
  (let [{:keys [community-id]} (<sub [:get-screen-params])
        sorted-categories (<sub [:communities/sorted-categories community-id])]
    (reset-data sorted-categories)
    (if (empty? sorted-categories)
      [community/blank-page (i18n/label :t/welcome-community-blank-message-edit-chats)]
      [:<> {:style {:flex 1}}
       [quo/separator]
       [draggable-list]])))